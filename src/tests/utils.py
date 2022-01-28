from pathlib import Path
from typing import List, Union

from pytest_multilog import TestHelper

from nmk.__main__ import nmk


class NmkTester(TestHelper):
    @property
    def nmk_cache(self) -> Path:
        return self.test_folder / "nmk"

    def template(self, name: str):
        return Path(__file__).parent / "templates" / name

    def nmk(self, project: Union[Path, str], with_logs: bool = False, extra_args: List[str] = None, expected_error: str = None):
        # Prepare args and run nmk
        if isinstance(project, str) and not project.startswith("http") and not project.startswith("github"):
            project = self.template(project)
        if isinstance(project, Path):
            project = project.as_posix()
        args = ["-c", self.nmk_cache.as_posix(), "-p", project]
        if not with_logs:
            args.append("--no-logs")
        if extra_args is not None:
            args.extend(extra_args)
        rc = nmk(args)

        # Expected OK?
        if expected_error is None:
            assert rc == 0, f"Unexpected nmk rc: {rc}"
        else:
            assert rc != 0, f"Unexpected nmk rc: {rc}"
            self.check_logs(f"nmk] ERROR 💀 - {expected_error.format(project=project)}")
