import time
from pathlib import Path
from typing import Dict, List

from .storage import StorageError, create_backend


class UploadManager:
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger

    def upload(self, local_file: Path) -> Dict[str, dict]:
        upload_config = self.config.get('upload', {})
        if not upload_config.get('enabled', True):
            return {}

        retry_count = int(upload_config.get('retry_count', 3))
        retry_interval = int(upload_config.get('retry_interval_seconds', 30))
        targets = self._enabled_targets(upload_config.get('targets', []))
        results: Dict[str, dict] = {}
        for target in targets:
            backend = create_backend(target)
            remote_path = backend.build_remote_path(local_file.name)
            results[backend.name] = self._upload_one(backend, local_file, remote_path, retry_count, retry_interval)
        return results

    def delete_remote(self, record: dict) -> int:
        deleted = 0
        targets_by_name = {item.get('name'): item for item in self._enabled_targets(self.config.get('upload', {}).get('targets', []))}
        for name, result in record.get('upload_results', {}).items():
            if result.get('status') != 'success':
                continue
            target = targets_by_name.get(name)
            if target is None:
                continue
            backend = create_backend(target)
            backend.delete(result.get('remote_path', ''))
            deleted += 1
        return deleted

    def _upload_one(self, backend, local_file: Path, remote_path: str, retry_count: int, retry_interval: int) -> dict:
        attempts = max(1, retry_count)
        last_error = None
        for index in range(1, attempts + 1):
            try:
                backend.upload(local_file, remote_path)
                return {'type': backend.config.get('type'), 'status': 'success', 'remote_path': remote_path, 'attempts': index}
            except Exception as exc:
                last_error = exc
                self.logger.warning(f'Upload to {backend.name} failed on attempt {index}/{attempts}: {exc}')
                if index < attempts:
                    time.sleep(retry_interval)
        return {'type': backend.config.get('type'), 'status': 'failed', 'remote_path': remote_path, 'error': str(last_error)}

    @staticmethod
    def _enabled_targets(targets: List[dict]) -> List[dict]:
        return [item for item in targets if item.get('enabled', True)]