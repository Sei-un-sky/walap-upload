import shutil
from pathlib import Path

from .base import StorageBackend


class LocalBackend(StorageBackend):
    def __init__(self, config: dict):
        super().__init__(config)
        self.directory = Path(str(config.get('directory', './remote_backups')))

    def upload(self, local_file: Path, remote_path: str) -> None:
        target = self.directory / remote_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_file, target)

    def test_connection(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def delete(self, remote_path: str) -> None:
        target = self.directory / remote_path
        if target.exists() and target.is_file():
            target.unlink()