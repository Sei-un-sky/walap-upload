import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from walap_upload.archive import create_world_zip
from walap_upload.config import Config
from walap_upload.metadata import MetadataStore
from walap_upload.retention import select_expired
from walap_upload.service import format_size
from walap_upload.service import BackupService
from walap_upload.snapshot import remove_snapshot, snapshot_world_dirs
from walap_upload.storage.local import LocalBackend
from walap_upload.uploader import UploadManager


class _FakeLogger:
    def info(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass

    def debug(self, message):
        pass


class _FakeServer:
    def __init__(self):
        self.commands = []
        self.logger = _FakeLogger()

    def execute(self, command):
        self.commands.append(command)


class CoreTests(unittest.TestCase):
    def test_create_world_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            world = root / 'world'
            world.mkdir()
            (world / 'level.dat').write_text('data', encoding='utf8')
            output = root / 'backup.zip'

            create_world_zip(output, [world], {'id': 'test'})

            self.assertTrue(output.exists())
            import zipfile
            with zipfile.ZipFile(output) as archive:
                self.assertIn('backup_info.json', archive.namelist())
                self.assertIn('world/level.dat', archive.namelist())

    def test_snapshot_world_dirs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            world = root / 'server' / 'world'
            nested = world / 'data'
            nested.mkdir(parents=True)
            (nested / 'level.dat').write_text('data', encoding='utf8')
            snapshot_root = root / 'backup_tmp' / 'snapshot'

            snapshot_dirs = snapshot_world_dirs([world], snapshot_root)

            self.assertEqual([path.name for path in snapshot_dirs], ['world'])
            self.assertEqual((snapshot_root / 'world' / 'data' / 'level.dat').read_text(encoding='utf8'), 'data')
            remove_snapshot(snapshot_root)
            self.assertFalse(snapshot_root.exists())

    def test_snapshot_world_dirs_support_multiple_worlds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            worlds = [root / name for name in ('world', 'world_nether')]
            for world in worlds:
                world.mkdir()
                (world / 'level.dat').write_text(world.name, encoding='utf8')
            snapshot_root = root / 'backup_tmp' / 'snapshot'

            snapshot_dirs = snapshot_world_dirs(worlds, snapshot_root)

            self.assertEqual([path.name for path in snapshot_dirs], ['world', 'world_nether'])
            self.assertEqual((snapshot_root / 'world' / 'level.dat').read_text(encoding='utf8'), 'world')
            self.assertEqual((snapshot_root / 'world_nether' / 'level.dat').read_text(encoding='utf8'), 'world_nether')

    def test_snapshot_world_dirs_reject_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / 'first' / 'world'
            second = root / 'second' / 'world'
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            snapshot_root = root / 'backup_tmp' / 'snapshot'

            with self.assertRaises(ValueError):
                snapshot_world_dirs([first, second], snapshot_root)

            self.assertFalse(snapshot_root.exists())

    def test_backup_resumes_world_save_when_snapshot_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'world').mkdir()
            config = Config({
                'server_name': 'test',
                'world_root': str(root),
                'world_dirs': ['world'],
                'backup': {
                    'local_dir': str(root / 'backups'),
                    'temp_dir': str(root / 'backup_tmp'),
                    'save_commands': True,
                    'calculate_sha256': False,
                },
                'upload': {'enabled': False},
                'retention': {'enabled': False},
            }, root / 'config', root)
            server = _FakeServer()
            metadata = MetadataStore(root / 'config' / 'metadata.json')

            with patch('walap_upload.service.snapshot_world_dirs', side_effect=OSError('copy failed')):
                BackupService(server, config, metadata)._run_backup_locked('manual')

            self.assertEqual(server.commands, ['save-off', 'save-all flush', 'save-on'])
            self.assertFalse(config.temp_dir.exists())
            self.assertEqual(metadata.last_record()['status'], 'failed')

    def test_backup_cleans_snapshot_when_archive_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            world = root / 'world'
            world.mkdir()
            (world / 'level.dat').write_text('data', encoding='utf8')
            config = Config({
                'server_name': 'test',
                'world_root': str(root),
                'world_dirs': ['world'],
                'backup': {
                    'local_dir': str(root / 'backups'),
                    'temp_dir': str(root / 'backup_tmp'),
                    'save_commands': True,
                    'calculate_sha256': False,
                },
                'upload': {'enabled': False},
                'retention': {'enabled': False},
            }, root / 'config', root)
            server = _FakeServer()
            metadata = MetadataStore(root / 'config' / 'metadata.json')

            with patch('walap_upload.service.create_world_zip', side_effect=OSError('archive failed')):
                BackupService(server, config, metadata)._run_backup_locked('manual')

            self.assertEqual(server.commands, ['save-off', 'save-all flush', 'save-on'])
            self.assertTrue(config.temp_dir.exists())
            self.assertEqual(list(config.temp_dir.iterdir()), [])
            self.assertEqual(metadata.last_record()['status'], 'failed')

    def test_metadata_store(self):
        with tempfile.TemporaryDirectory() as temp:
            store = MetadataStore(Path(temp) / 'metadata.json')
            store.add_record({'id': '1', 'created_at': '2026-01-01T00:00:00+00:00', 'status': 'running'})
            store.update_record('1', {'status': 'uploaded'})
            self.assertEqual(store.last_record()['status'], 'uploaded')

    def test_retention(self):
        records = [
            {'id': 'old', 'created_at': '2000-01-01T00:00:00+00:00'},
            {'id': 'new', 'created_at': '2999-01-01T00:00:00+00:00'},
            {'id': 'done', 'created_at': '1999-01-01T00:00:00+00:00', 'retention_deleted': True},
        ]
        expired = select_expired(records, keep_last=1, keep_days=30)
        self.assertEqual([item['id'] for item in expired], ['old'])

    def test_local_backend_upload_and_delete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'backup.zip'
            source.write_bytes(b'backup')
            backend = LocalBackend({'name': 'local', 'type': 'local', 'directory': str(root / 'remote')})
            backend.upload(source, 'server/backup.zip')
            self.assertTrue((root / 'remote' / 'server' / 'backup.zip').exists())
            backend.delete('server/backup.zip')
            self.assertFalse((root / 'remote' / 'server' / 'backup.zip').exists())

    def test_test_connections(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logger = _FakeLogger()
            config = {
                'upload': {
                    'enabled': True,
                    'targets': [
                        {'name': 'local', 'type': 'local', 'enabled': True, 'directory': str(root / 'remote')},
                        {'name': 'disabled', 'type': 'local', 'enabled': False, 'directory': str(root / 'disabled')},
                        {'name': 'unknown', 'type': 'unknown', 'enabled': True},
                    ],
                },
            }

            results = UploadManager(config, logger).test_connections()

            self.assertEqual(results['local']['status'], 'success')
            self.assertEqual(results['unknown']['status'], 'failed')
            self.assertNotIn('disabled', results)
            self.assertTrue((root / 'remote').exists())

    def test_world_dirs_support_glob(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            server_root = root / 'server'
            server_root.mkdir()
            (server_root / 'world').mkdir()
            (server_root / 'world_nether').mkdir()
            (server_root / 'logs').mkdir()
            config = Config({'world_root': './server', 'world_dirs': ['world*']}, root / 'config', root)

            names = [path.name for path in config.world_dirs]

            self.assertEqual(names, ['world', 'world_nether'])

    def test_format_size(self):
        self.assertEqual(format_size(12), '12 B')
        self.assertEqual(format_size(2048), '2.00 KiB')
        self.assertEqual(format_size(3 * 1024 * 1024), '3.00 MiB')

    def test_language_config_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = Config({'server_name': 'test', 'language': 'en', 'world_dirs': []}, root / 'config', root)
            config.set_language('cn')

            data = json.loads((root / 'config' / 'config.json').read_text(encoding='utf8'))
            self.assertEqual(data['language'], 'cn')
            self.assertEqual(config.language, 'cn')


if __name__ == '__main__':
    unittest.main()