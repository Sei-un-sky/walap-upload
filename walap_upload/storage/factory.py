from .base import StorageError
from .ftp import FtpBackend
from .local import LocalBackend
from .placeholder import PlaceholderBackend
from .sftp import SftpBackend
from .webdav import WebDavBackend


def create_backend(config: dict):
    backend_type = str(config.get('type', '')).lower()
    if backend_type == 'local':
        return LocalBackend(config)
    if backend_type == 'ftp':
        return FtpBackend(config, use_tls=False)
    if backend_type == 'ftps':
        return FtpBackend(config, use_tls=True)
    if backend_type == 'sftp':
        return SftpBackend(config)
    if backend_type == 'webdav':
        return WebDavBackend(config)
    if backend_type in {'s3', 'baidu', 'baidu_netdisk', 'unicom', 'china_unicom_netdisk'}:
        return PlaceholderBackend(config)
    raise StorageError(f'Unsupported storage backend type: {backend_type}')