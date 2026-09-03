import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / 'dist'
METADATA_FILE = ROOT / 'mcdreforged.plugin.json'
PACKAGE_DIR = ROOT / 'walap_upload'


def iter_package_files():
    yield METADATA_FILE
    for path in sorted(PACKAGE_DIR.rglob('*.py')):
        if '__pycache__' not in path.parts:
            yield path
    for relative in [
        'LICENSE',
        'README.md',
        'README_CN.md',
        'RELEASE_NOTES.md',
        'docs/INSTALL.md',
        'docs/INSTALL_CN.md',
        'docs/USAGE.md',
        'docs/USAGE_CN.md',
    ]:
        path = ROOT / relative
        if path.exists():
            yield path


def validate_archive(archive_path: Path) -> None:
    required = {
        'mcdreforged.plugin.json',
        'walap_upload/__init__.py',
    }
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f'Archive is missing required files: {", ".join(missing)}')


def main() -> int:
    metadata = json.loads(METADATA_FILE.read_text(encoding='utf8'))
    plugin_id = metadata['id']
    version = metadata['version']
    archive_path = DIST_DIR / f'{plugin_id}-v{version}.mcdr'

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_package_files():
            archive.write(path, path.relative_to(ROOT).as_posix())

    validate_archive(archive_path)
    print(archive_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())