from pathlib import Path

from .base import StorageBackend, StorageError


class PlaceholderBackend(StorageBackend):
    def upload(self, local_file: Path, remote_path: str) -> None:
        backend_type = self.config.get('type')
        raise StorageError(f'{backend_type} backend is reserved but not implemented in version 0.3.0')

    def test_connection(self) -> None:
        backend_type = self.config.get('type')
        raise StorageError(f'{backend_type} backend is reserved but not implemented in version 0.3.0')

    def delete(self, remote_path: str) -> None:
        backend_type = self.config.get('type')
        raise StorageError(f'{backend_type} backend is reserved but not implemented in version 0.3.0')