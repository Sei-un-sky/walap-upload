import json
import zipfile
from pathlib import Path
from typing import Dict, Iterable


def create_world_zip(output_file: Path, world_dirs: Iterable[Path], backup_info: Dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('backup_info.json', json.dumps(backup_info, indent=2))
        for world_dir in world_dirs:
            if not world_dir.exists():
                continue
            base_name = world_dir.name
            for path in world_dir.rglob('*'):
                if path.is_file():
                    archive.write(path, Path(base_name) / path.relative_to(world_dir))