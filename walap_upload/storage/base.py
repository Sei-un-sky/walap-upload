from pathlib import Path


class StorageError(RuntimeError):
    pass


class StorageBackend:
    def __init__(self, config: dict):
        self.config = config
        self.name = str(config.get('name', config.get('type', 'unnamed')))
        self.remote_prefix = str(config.get('remote_prefix', '')).strip('/')

    def build_remote_path(self, file_name: str) -> str:
        if self.remote_prefix:
            return f'{self.remote_prefix}/{file_name}'
        return file_name

    def upload(self, local_file: Path, remote_path: str) -> None:
        raise NotImplementedError

    def delete(self, remote_path: str) -> None:
        raise NotImplementedError