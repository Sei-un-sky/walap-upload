import json
import tempfile
import unittest
from pathlib import Path

from walap_upload.archive import create_world_zip
from walap_upload.config import Config
from walap_upload.metadata import MetadataStore
from walap_upload.retention import select_expired
from walap_upload.service import format_size
from walap_upload.storage.local import LocalBackend


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