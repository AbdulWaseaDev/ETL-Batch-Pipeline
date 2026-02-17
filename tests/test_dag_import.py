from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def test_etl_dag_import_and_structure():
    dag_file = Path(__file__).resolve().parents[1] / "dags" / "etl_dag.py"
    spec = spec_from_file_location("etl_dag", dag_file)
    assert spec is not None and spec.loader is not None

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    dag = getattr(module, "dag", None)
    assert dag is not None
    assert dag.dag_id == "batch_etl_pipeline"

    tasks = {task.task_id: task for task in dag.tasks}
    assert set(tasks.keys()) == {"extract", "transform", "upload_to_s3", "load"}

    assert tasks["extract"].downstream_task_ids == {"transform"}
    assert tasks["transform"].downstream_task_ids == {"upload_to_s3"}
    assert tasks["upload_to_s3"].downstream_task_ids == {"load"}
    assert tasks["load"].downstream_task_ids == set()
