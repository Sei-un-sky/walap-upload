import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetadataStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({'backups': []})

    def add_record(self, record: Dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            data['backups'].append(record)
            data['backups'].sort(key=lambda item: item.get('created_at', ''), reverse=True)
            self._write(data)

    def update_record(self, backup_id: str, patch: Dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            for item in data['backups']:
                if item.get('id') == backup_id:
                    item.update(patch)
                    break
            self._write(data)

    def list_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            records = list(self._read().get('backups', []))
        return records if limit is None else records[:limit]

    def last_record(self) -> Optional[Dict[str, Any]]:
        records = self.list_records(limit=1)
        return records[0] if records else None

    def _read(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text(encoding='utf8'))

    def _write(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding='utf8')