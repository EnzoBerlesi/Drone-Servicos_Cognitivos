#!/usr/bin/env python3
"""Runner de testes que imprime resultado por teste no formato:
teste <nome> = <resultado>

Uso: python scripts/run_tests_report.py
"""
import sys
import pytest


class SimpleReportPlugin:
    def __init__(self):
        self.results = []

    def pytest_runtest_logreport(self, report):
        # only consider the call phase (actual test execution)
        if report.when == 'call':
            # report.outcome is one of 'passed', 'failed', 'skipped'
            self.results.append((report.nodeid, report.outcome))

    def pytest_sessionfinish(self, session, exitstatus):
        # print each test result in the requested format
        for nodeid, outcome in self.results:
            # simplify nodeid to file::testname
            print(f"{nodeid} = {outcome}")

        passed = sum(1 for _, o in self.results if o == 'passed')
        failed = sum(1 for _, o in self.results if o == 'failed')
        skipped = sum(1 for _, o in self.results if o == 'skipped')
        print()
        print(f"Resumo: passed={passed} failed={failed} skipped={skipped}")


def main(argv=None):
    argv = argv or sys.argv[1:]
    # default: run all tests in tests/
    args = argv or ["tests"]
    plugin = SimpleReportPlugin()
    # run pytest with our plugin
    rc = pytest.main(args + ["-q"], plugins=[plugin])
    # exit with pytest return code so CI understands failures
    raise SystemExit(rc)


if __name__ == '__main__':
    main()
