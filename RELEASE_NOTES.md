# Walap Upload v0.2.1

## Improvements

- Copy world data to a temporary snapshot while saving is paused.
- Resume world saving before zip compression and upload start.
- Add `!!wp test` to test enabled remote storage connections without uploading a backup.
- Clean up temporary snapshots after successful and failed backups.

## Compatibility

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- `paramiko` is required only for the `sftp` backend.

# Walap Upload v0.3.0

## Improvements

- Copy world data to a temporary snapshot while saving is paused.
- Resume world saving before zip compression and upload start.
- Clean up temporary snapshots after successful and failed backups.

## Compatibility

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- `paramiko` is required only for the `sftp` backend.

# Walap Upload v0.2.0

Packaging fix release for Walap Upload.

## Fixes

- Added an explicit MCDReforged entrypoint: `walap_upload`.
- Added a repeatable `.mcdr` build script with archive structure validation.
- Ensured the release archive contains `walap_upload/__init__.py` at the archive root.

## Compatibility

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- `paramiko` is required only for the `sftp` backend.

# Walap Upload v0.1.0

Initial release of Walap Upload, an MCDReforged plugin for automatic Minecraft world backup uploads.

## Scope

- Archive complete world folders into a single zip file.
- Upload backups to remote storage.
- Manage backup metadata and retention cleanup.
- No automatic rollback or restore. Restore is intentionally manual.

## Features

- `!!wp` command help.
- `!!wp now`, `!!wp list`, `!!wp status`, `!!wp clean`, `!!wp reload`.
- `!!wp cn` and `!!wp en` for command output language switching.
- Scheduled interval backups.
- World folder matching through `world_root` and glob patterns such as `world*`.
- Minecraft save flow: `save-off`, `save-all flush`, archive, `save-on`, then upload.
- Adaptive file size display, for example `KiB`, `MiB`, and `GiB`.
- Metadata record file for backup status and uploaded targets.
- Retention cleanup by `keep_last` and `keep_days`.

## Storage Backends

Implemented:

- `local`
- `webdav`
- `ftp`
- `ftps`
- `sftp`

Reserved for future versions:

- `s3`
- `baidu`
- `unicom`

For Baidu Netdisk, China Unicom Netdisk, and other netdisks in `v0.1.0`, the recommended route is Alist/WebDAV.

## Install

See:

- `INSTALL.md`
- `INSTALL_CN.md`

## Compatibility

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- `paramiko` is required only for the `sftp` backend.