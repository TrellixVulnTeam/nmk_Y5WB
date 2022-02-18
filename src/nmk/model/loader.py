import json
import os
import shutil
import sys
from argparse import Namespace
from pathlib import Path

from nmk.errors import NmkNoLogsError
from nmk.logs import NmkLogger, logging_setup
from nmk.model.config import NmkStaticConfig
from nmk.model.files import NmkModelFile
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel


class NmkLoader:
    def __init__(self, args: Namespace, with_logs: bool = True):
        # Finish args parsing
        self.finish_parsing(args, with_logs)

        # Prepare repo cache and empty model
        self.repo_cache: Path = args.nmk_dir / "cache"
        self.model = NmkModel(args)

        # Load model
        self.load_model_from_files()

        # Override config from args
        self.override_config()

        # Validate tasks after full loading process
        self.validate_tasks()

    def load_model_from_files(self):
        # Add built-in config items
        root = self.model.args.root.resolve()
        for name, value in {
            NmkRootConfig.PYTHON_PATH: [],
            NmkRootConfig.BASE_DIR: "",  # Useless while directly referenced (must identify current project file parent dir)
            NmkRootConfig.ROOT_DIR: root,
            NmkRootConfig.CACHE_DIR: root / ".nmk",
            NmkRootConfig.PROJECT_DIR: "",  # Will be updated as soon as initial project is loaded
            NmkRootConfig.PROJECT_FILES: [],  # Will be updated as soon as files are loaded
            NmkRootConfig.ENV: {k: v for k, v in os.environ.items()},
        }.items():
            self.model.add_config(name, None, value)

        # Init recursive files loading loop
        NmkModelFile(self.model.args.project, self.repo_cache, self.model, [])

        # Refresh project files list
        NmkLogger.debug(f"Updating {NmkRootConfig.PROJECT_FILES} now that all files are loaded")
        self.model.config[NmkRootConfig.PROJECT_FILES] = NmkStaticConfig(NmkRootConfig.PROJECT_FILES, self.model, None, list(self.model.files.keys()))

    def override_config(self):
        # Load json fragment from config arg, if any
        try:
            override_config = json.loads(self.model.args.config) if self.model.args.config is not None else {}
        except Exception as e:
            raise Exception(f"Invalid Json fragment for --config option: {e}")
        assert isinstance(override_config, dict), "Json fragment for --config option must be an object"

        # Override model config with command-line values
        if len(override_config):
            NmkLogger.debug("Overriding config from --config option")
            for k, v in override_config.items():
                self.model.add_config(k, None, v)

    def finish_parsing(self, args: Namespace, with_logs: bool):
        # Handle root folder
        if args.root is None:  # pragma: no cover
            # By default, root dir is the parent folder of currently running venv
            if sys.prefix == sys.base_prefix:
                raise NmkNoLogsError("nmk must run from a virtual env; can't find root dir")
            args.root = Path(sys.prefix).parent
        else:
            # Verify custom root
            if not args.root.is_dir():
                raise NmkNoLogsError(f"specified root directory not found: {args.root}")

        # Handle cache clear
        args.nmk_dir = args.root / ".nmk"
        if args.no_cache and args.nmk_dir.is_dir():
            shutil.rmtree(args.nmk_dir)

        # Setup logging
        if with_logs:
            logging_setup(args)

    def validate_tasks(self):
        # Iterate on tasks
        for task in self.model.tasks.values():
            # Resolve references
            task._resolve_subtasks()
            task._resolve_contribs()
