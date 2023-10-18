from functools import partial

from invoke import task
from invoke.exceptions import UnexpectedExit
from invoke_common_tasks import *

MAIN_CODE_PATH = "src/"
UNIT_TEST_PATH = "tests/"
TEST_PATHS = [UNIT_TEST_PATH]
CODE_PATHS = [MAIN_CODE_PATH, UNIT_TEST_PATH]


@task
def install_hooks(c):
    c.run("pre-commit install --install-hooks -t pre-commit -t pre-push")


@task
def run_flake8(c):
    c.run(f"flake8 --select F401 {' '.join(CODE_PATHS)}")


@task
def run_isort(c, check=False):
    c.run(f"isort .{' --check --profile=black' if check else ''}")


@task
def run_black(c, check=False):
    c.run(f"black .{' --check' if check else ''}")


@task
def run_pyupgrade(c):
    c.run("pyupgrade --py39-plus")


@task
def run_mypy(c):
    c.run(f"mypy {' '.join(CODE_PATHS)}")


@task
def format(c):
    run_pyupgrade(c)
    run_isort(c, check=False)
    run_black(c, check=False)


@task
def lint(c):
    commands = (
        partial(run_isort, check=True),
        partial(run_black, check=True),
        run_flake8,
        run_mypy,
    )
    exit_code = 0
    for cmd in commands:
        try:
            cmd(c)
        except UnexpectedExit as err:
            exit_code = err.result.return_code
    if exit_code:
        exit(exit_code)


def pytest_coverage(c, paths):
    c.run(
        f"""pytest \
        --cov-report=xml \
        --cov-report=term-missing \
        --junitxml=test-result.xml \
        --cov={MAIN_CODE_PATH} \
        {paths}"""
    )


@task
def unit(c):
    pytest_coverage(c, UNIT_TEST_PATH)


@task
def test(c):
    unit(c)


@task
def test_all(c):
    pytest_coverage(c, " ".join(TEST_PATHS))


@task
def build(c):
    c.run("poetry build")
