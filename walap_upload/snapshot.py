import shutil
from pathlib import Path
from typing import Iterable, List


def snapshot_world_dirs(world_dirs: Iterable[Path], snapshot_root: Path) -> List[Path]:
    world_dirs = list(world_dirs)
    names = [world_dir.name for world_dir in world_dirs]
    if len(names) != len(set(names)):
        raise ValueError('World directory names must be unique')
    remove_snapshot(snapshot_root)
    snapshot_root.mkdir(parents=True, exist_ok=True)
    snapshot_dirs: List[Path] = []
    for world_dir in world_dirs:
        target_dir = snapshot_root / world_dir.name
        _copy_tree(world_dir, target_dir)
        snapshot_dirs.append(target_dir)
    return snapshot_dirs


def remove_snapshot(snapshot_root: Path) -> None:
    shutil.rmtree(snapshot_root, ignore_errors=True)


def _copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in source.rglob('*'):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)