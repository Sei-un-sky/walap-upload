import copy
import glob
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONFIG: Dict[str, Any] = {
    'server_name': 'survival',
    'language': 'en',
    'world_root': './server',
    'world_dirs': ['world*'],
    'backup': {
        'enabled': True,
        'interval_hours': 6,
        'format': 'zip',
        'temp_dir': './backup_tmp',
        'local_dir': './backups',
        'keep_local_after_upload': True,
        'calculate_sha256': True,
        'save_commands': True,
    },
    'upload': {
        'enabled': True,
        'mode': 'all',
        'retry_count': 3,
        'retry_interval_seconds': 30,
        'targets': [
            {
                'name': 'local_test',
                'type': 'local',
                'enabled': True,
                'directory': './remote_backups',
                'remote_prefix': 'survival/'
            }
        ]
    },
    'retention': {
        'enabled': True,
        'keep_last': 10,
        'keep_days': 30,
        'delete_local': True,
        'delete_remote': False
    }
}


@dataclass
class Config:
    data: Dict[str, Any]
    config_dir: Path
    server_dir: Path

    @classmethod
    def load(cls, server):
        config_dir = Path(server.get_data_folder())
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / 'config.json'
        if not config_file.exists():
            config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding='utf8')
            server.logger.info(f'Created default config: {config_file}')
        raw = json.loads(config_file.read_text(encoding='utf-8-sig'))
        data = _merge_dict(copy.deepcopy(DEFAULT_CONFIG), raw)
        return cls(data=data, config_dir=config_dir, server_dir=Path.cwd())

    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / 'config.json'
        config_file.write_text(json.dumps(self.data, indent=2), encoding='utf8')

    @property
    def server_name(self) -> str:
        return str(self.data['server_name'])

    @property
    def language(self) -> str:
        language = str(self.data.get('language', 'en')).lower()
        return 'cn' if language in {'cn', 'zh', 'zh_cn'} else 'en'

    def set_language(self, language: str) -> None:
        normalized = 'cn' if language.lower() in {'cn', 'zh', 'zh_cn'} else 'en'
        self.data['language'] = normalized
        self.save()

    @property
    def world_dirs(self) -> List[Path]:
        result: List[Path] = []
        seen = set()
        for item in self.data['world_dirs']:
            for path in self.expand_world_entry(str(item)):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    result.append(resolved)
        return result

    @property
    def world_root(self) -> Path:
        return self.resolve_path(str(self.data.get('world_root', './server')))

    @property
    def metadata_file(self) -> Path:
        return self.config_dir / 'metadata.json'

    @property
    def backup_dir(self) -> Path:
        return self.resolve_path(self.data['backup']['local_dir'])

    @property
    def temp_dir(self) -> Path:
        return self.resolve_path(self.data['backup']['temp_dir'])

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.server_dir / path

    def expand_world_entry(self, value: str) -> List[Path]:
        if not glob.has_magic(value):
            path = Path(value)
            if path.is_absolute():
                return [path]
            return [self.world_root / path]
        if Path(value).is_absolute():
            matches = glob.glob(value, recursive=True)
            return [Path(item) for item in sorted(matches) if Path(item).is_dir()]
        return [path for path in sorted(self.world_root.glob(value)) if path.is_dir()]


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dict(base[key], value)
        else:
            base[key] = value
    return base