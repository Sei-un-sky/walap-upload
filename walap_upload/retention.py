from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set


def select_expired(records: Iterable[Dict], keep_last: int, keep_days: int) -> List[Dict]:
    items = sorted(records, key=lambda item: item.get('created_at', ''), reverse=True)
    keep_ids: Set[str] = set()
    for item in items[:max(0, keep_last)]:
        keep_ids.add(item.get('id'))

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(0, keep_days))
    for item in items:
        created_at = _parse_datetime(item.get('created_at'))
        if created_at is not None and created_at >= cutoff:
            keep_ids.add(item.get('id'))

    return [
        item for item in items
        if item.get('id') not in keep_ids
        and not item.get('protected', False)
        and not item.get('retention_deleted', False)
    ]


def delete_local_file(path_value: str) -> bool:
    if not path_value:
        return False
    path = Path(path_value)
    if path.exists() and path.is_file():
        path.unlink()
        return True
    return False


def _parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)