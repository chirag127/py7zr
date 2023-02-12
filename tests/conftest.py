# Configuration for pytest to automatically collect types.
# Thanks to Guilherme Salgado.
import os

import cpuinfo
import pytest
from pyannotate_runtime import collect_types


def pytest_collection_finish(session):
    """Handle the pytest collection finish hook: configure pyannotate.
    Explicitly delay importing `collect_types` until all tests have
    been collected.  This gives gevent a chance to monkey patch the
    world before importing pyannotate.
    """
    collect_types.init_types_collection()


@pytest.fixture(autouse=True)
def collect_types_fixture():
    collect_types.start()
    yield
    collect_types.stop()


def pytest_sessionfinish(session, exitstatus):
    os.makedirs("build/", exist_ok=True)
    collect_types.dump_stats("build/type_info.json")


def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Calculate compression/decompression speed and add as extra_info"""
    for benchmark in output_json["benchmarks"]:
        if "data_size" in benchmark["extra_info"]:
            rate = benchmark["extra_info"].get("data_size", 0.0) / benchmark["stats"]["mean"]
            benchmark["extra_info"]["rate"] = rate


def pytest_benchmark_update_machine_info(config, machine_info):
    cpu_info = cpuinfo.get_cpu_info()
    brand = cpu_info.get("brand_raw", None)
    if brand is None:
        brand = f'{cpu_info.get("count", "unknown")} core(s) {cpu_info.get("arch", "unknown")} CPU '
    machine_info["cpu"]["brand"] = brand
    machine_info["cpu"]["hz_actual_friendly"] = cpu_info.get("hz_actual_friendly", "unknown")


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        # --run-slow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
