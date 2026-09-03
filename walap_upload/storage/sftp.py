from pathlib import Path, PurePosixPath

from .base import StorageBackend, StorageError


class SftpBackend(StorageBackend):
    def upload(self, local_file: Path, remote_path: str) -> None:
        with self._connect() as client:
            sftp = client.open_sftp()
            try:
                final_path = self._full_remote_path(remote_path)
                self._ensure_dirs(sftp, str(PurePosixPath(final_path).parent))
                sftp.put(str(local_file), final_path)
            finally:
                sftp.close()

    def test_connection(self) -> None:
        client = self._connect()
        client.close()

    def delete(self, remote_path: str) -> None:
        with self._connect() as client:
            sftp = client.open_sftp()
            try:
                sftp.remove(self._full_remote_path(remote_path))
            except FileNotFoundError:
                pass
            finally:
                sftp.close()

    def _connect(self):
        try:
            import paramiko
        except ModuleNotFoundError as exc:
            raise StorageError('SFTP backend requires paramiko. Install paramiko in the MCDR Python environment.') from exc

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=str(self.config['host']),
            port=int(self.config.get('port', 22)),
            username=str(self.config['username']),
            password=str(self.config.get('password', '')) or None,
            key_filename=self.config.get('key_filename'),
            timeout=int(self.config.get('timeout', 60)),
            banner_timeout=int(self.config.get('banner_timeout', 60)),
            auth_timeout=int(self.config.get('auth_timeout', 60)),
        )
        return client

    def _full_remote_path(self, remote_path: str) -> str:
        base_dir = str(self.config.get('base_dir', '')).strip()
        if not base_dir:
            return remote_path
        return str(PurePosixPath(base_dir) / remote_path)

    @staticmethod
    def _ensure_dirs(sftp, directory: str) -> None:
        if directory in {'', '.'}:
            return
        current = '/' if directory.startswith('/') else ''
        for part in PurePosixPath(directory).parts:
            if part == '/':
                continue
            current = str(PurePosixPath(current) / part) if current else part
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)