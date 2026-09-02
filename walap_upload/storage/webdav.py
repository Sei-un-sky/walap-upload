import base64
import http.client
from pathlib import Path
from urllib.parse import quote, urlsplit

from .base import StorageBackend, StorageError


class WebDavBackend(StorageBackend):
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = str(config['url']).rstrip('/')
        self.username = str(config.get('username', ''))
        self.password = str(config.get('password', ''))
        self.timeout = int(config.get('timeout', 120))

    def upload(self, local_file: Path, remote_path: str) -> None:
        self._ensure_dirs(remote_path)
        with local_file.open('rb') as file:
            status, reason, _ = self._request('PUT', remote_path, body=file, content_length=local_file.stat().st_size)
        if status not in {200, 201, 204}:
            raise StorageError(f'WebDAV PUT failed: {status} {reason}')

    def delete(self, remote_path: str) -> None:
        status, reason, _ = self._request('DELETE', remote_path)
        if status not in {200, 202, 204, 404}:
            raise StorageError(f'WebDAV DELETE failed: {status} {reason}')

    def _ensure_dirs(self, remote_path: str) -> None:
        parts = [part for part in remote_path.split('/')[:-1] if part]
        current = ''
        for part in parts:
            current = f'{current}/{part}' if current else part
            status, reason, _ = self._request('MKCOL', current)
            if status not in {201, 405}:
                raise StorageError(f'WebDAV MKCOL failed for {current}: {status} {reason}')

    def _request(self, method: str, remote_path: str, body=None, content_length: int = 0):
        parsed = urlsplit(self.base_url)
        conn_cls = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
        conn = conn_cls(parsed.netloc, timeout=self.timeout)
        base_path = parsed.path.rstrip('/')
        full_path = f'{base_path}/{quote(remote_path, safe="/")}'
        headers = {}
        if self.username or self.password:
            token = base64.b64encode(f'{self.username}:{self.password}'.encode('utf8')).decode('ascii')
            headers['Authorization'] = f'Basic {token}'
        if content_length:
            headers['Content-Length'] = str(content_length)
        conn.request(method, full_path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, response.reason, data