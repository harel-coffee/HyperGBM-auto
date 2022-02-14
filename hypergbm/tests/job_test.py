import sys
import sys
import tempfile
from pathlib import Path

from hypernets.hyperctl import daemon
from hypernets.hyperctl import get_context
from hypernets.hyperctl.batch import ShellJob
from hypernets.hyperctl.executor import LocalExecutorManager

test_source_dir = __file__

def test_create_hypergbm_experiment_job():
    batches_data_dir = tempfile.mkdtemp(prefix="hypergbm-test-batches")
    from hypernets.tabular.datasets.dsutils import basedir

    job_name = "eVqNV5Uo0"
    batch_name = "eVqNV5Ut"
    source_dir = (Path(test_source_dir).parent.parent).as_posix()
    print(source_dir)
    config_dict = {
        "jobs": [
            {
                "name": job_name,
                "params": {
                    "train_data": f'{basedir}/blood.csv',
                    "target": "Class",
                    "report_render": 'excel',
                },
                "execution": {
                    "command": f"PYTHONPATH={source_dir};{sys.executable} -m hypergbm.job"
                }
            }
        ],
        "backend": {
            "type": "local",
            "conf": {}
        },
        "name": batch_name,
        "daemon": {
            "port": 8061,
            "exit_on_finish": True
        },
        "version": 2.5
    }

    print("Config:")
    print(config_dict)

    daemon.run_batch(config_dict, batches_data_dir)

    executor_manager = get_context().executor_manager
    assert isinstance(executor_manager, LocalExecutorManager)

    from hypernets.tests.hyperctl.test_daemon import assert_batch_finished
    assert_batch_finished(get_context().batch, batch_name, [job_name], ShellJob.STATUS_SUCCEED)

    assert (Path(batches_data_dir) / batch_name / job_name / "report.xlsx").exists()