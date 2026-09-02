import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

from .archive import create_world_zip
from .config import Config
from .hash_utils import sha256_file
from .metadata import MetadataStore
from .retention import delete_local_file, select_expired
from .uploader import UploadManager


class BackupService:
    def __init__(self, server, config: Config, metadata: MetadataStore):
        self.server = server
        self.config = config
        self.metadata = metadata
        self._lock = threading.Lock()
        self._running = False

    def reload_config(self) -> None:
        self.config = Config.load(self.server)

    def is_running(self) -> bool:
        return self._running

    def submit_backup(self, trigger: str) -> bool:
        if self._running:
            self.server.logger.warning('Backup is already running')
            return False
        thread = threading.Thread(target=self.run_backup, args=(trigger,), name='walap-upload-backup', daemon=True)
        thread.start()
        return True

    def run_backup(self, trigger: str) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
        try:
            self._run_backup_locked(trigger)
        finally:
            self._running = False

    def clean_old_backups(self) -> dict:
        retention_config = self.config.data.get('retention', {})
        if not retention_config.get('enabled', True):
            return {'local_deleted': 0, 'remote_deleted': 0}
        expired = select_expired(
            self.metadata.list_records(),
            int(retention_config.get('keep_last', 10)),
            int(retention_config.get('keep_days', 30)),
        )
        local_deleted = 0
        remote_deleted = 0
        uploader = UploadManager(self.config.data, self.server.logger)
        for record in expired:
            record_local_deleted = False
            record_remote_deleted = 0
            if retention_config.get('delete_local', True):
                record_local_deleted = delete_local_file(record.get('local_path', ''))
                local_deleted += 1 if record_local_deleted else 0
            if retention_config.get('delete_remote', False):
                try:
                    record_remote_deleted = uploader.delete_remote(record)
                    remote_deleted += record_remote_deleted
                except Exception as exc:
                    self.server.logger.warning(f"Failed to delete remote backup {record.get('id')}: {exc}")
            self.metadata.update_record(record.get('id'), {
                'retention_deleted': True,
                'local_deleted': record_local_deleted,
                'remote_deleted_count': record_remote_deleted,
            })
        return {'local_deleted': local_deleted, 'remote_deleted': remote_deleted}

    def _run_backup_locked(self, trigger: str) -> None:
        created_at = datetime.now(timezone.utc).astimezone()
        backup_id = created_at.strftime('%Y%m%d-%H%M%S')
        file_name = f"{self.config.server_name}_full_{created_at.strftime('%Y-%m-%d_%H-%M-%S')}_{trigger}.zip"
        output_file = self.config.backup_dir / file_name
        world_dirs = [path for path in self.config.world_dirs if path.exists() and path.is_dir()]
        if not world_dirs:
            raise RuntimeError('No world directories matched config world_dirs')
        record = {
            'id': backup_id,
            'server_name': self.config.server_name,
            'created_at': created_at.isoformat(),
            'trigger': trigger,
            'file_name': file_name,
            'local_path': str(output_file),
            'status': 'running',
            'world_dirs': [str(path) for path in world_dirs],
        }
        self.metadata.add_record(record)
        try:
            self._prepare_world_save()
            try:
                create_world_zip(output_file, world_dirs, record)
            finally:
                self._resume_world_save()

            size = output_file.stat().st_size
            self.server.logger.info(f'World save resumed. Archive is ready: {file_name} ({format_size(size)}). Starting upload.')
            patch = {'size': size, 'status': 'archived'}
            if self.config.data['backup'].get('calculate_sha256', True):
                patch['sha256'] = sha256_file(output_file)
            self.metadata.update_record(backup_id, patch)

            uploader = UploadManager(self.config.data, self.server.logger)
            upload_results = uploader.upload(output_file)
            final_status = 'uploaded'
            if upload_results and any(item.get('status') != 'success' for item in upload_results.values()):
                final_status = 'partial_failed'
            self.metadata.update_record(backup_id, {'upload_results': upload_results, 'status': final_status})
            cleanup = self.clean_old_backups()
            self.server.logger.info(f'Backup {backup_id} finished: {final_status}, cleanup={cleanup}')
        except Exception as exc:
            self.metadata.update_record(backup_id, {'status': 'failed', 'error': str(exc)})
            self.server.logger.error(f'Backup {backup_id} failed: {exc}')
            self.server.logger.debug(traceback.format_exc())

    def _prepare_world_save(self) -> None:
        if self.config.data['backup'].get('save_commands', True):
            self.server.execute('save-off')
            self.server.execute('save-all flush')

    def _resume_world_save(self) -> None:
        if self.config.data['backup'].get('save_commands', True):
            self.server.execute('save-on')


def format_size(size: int) -> str:
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == 'B':
                return f'{int(value)} B'
            return f'{value:.2f} {unit}'
        value /= 1024