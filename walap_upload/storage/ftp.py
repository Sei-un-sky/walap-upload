import ftplib
from pathlib import Path, PurePosixPath

from .base import StorageBackend


class FtpBackend(StorageBackend):
    def __init__(self, config: dict, use_tls: bool):
        super().__init__(config)
        self.use_tls = use_tls

    def upload(self, local_file: Path, remote_path: str) -> None:
        with self._connect() as ftp:
            self._ensure_dirs(ftp, str(PurePosixPath(remote_path).parent))
            with local_file.open('rb') as file:
                ftp.storbinary(f'STOR {remote_path}', file)

    def delete(self, remote_path: str) -> None:
        with self._connect() as ftp:
            try:
                ftp.delete(remote_path)
            except ftplib.error_perm as exc:
                if not str(exc).startswith('550'):
                    raise

    def _connect(self):
        cls = ftplib.FTP_TLS if self.use_tls else ftplib.FTP
        ftp = cls()
        ftp.connect(str(self.config['host']), int(self.config.get('port', 990 if self.use_tls else 21)), timeout=int(self.config.get('timeout', 60)))
        ftp.login(str(self.config['username']), str(self.config['password']))
        if self.use_tls:
            ftp.prot_p()
        return ftp

    @staticmethod
    def _ensure_dirs(ftp, directory: str) -> None:
        if directory in {'', '.'}:
            return
        current = ''
        for part in PurePosixPath(directory).parts:
            if part == '/':
                continue
            current = f'{current}/{part}' if current else part
            try:
                ftp.mkd(current)
            except ftplib.error_perm as exc:
                if not str(exc).startswith('550'):
                    raise