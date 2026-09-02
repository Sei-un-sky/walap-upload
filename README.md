# Walap Upload

MCDReforged plugin for automatic Minecraft world backups.

Version `0.1.0` focuses on one job: archive the full world directories and upload the zip file to remote storage. It does not provide rollback or automatic restore.

Chinese documentation: [README_CN.md](README_CN.md)

Installation guides: [INSTALL.md](INSTALL.md) / [INSTALL_CN.md](INSTALL_CN.md)

Release notes: [RELEASE_NOTES.md](RELEASE_NOTES.md)

## Features

- Manual command: `!!wp now`
- `!!wp` help output and English/Chinese command messages
- Scheduled backup by interval
- Full world zip archive
- Minecraft save commands around archiving: `save-off`, `save-all flush`, archive, then `save-on`
- Upload starts after `save-on`, so the game can continue saving while the upload is running
- Upload backends as independent modules
- Built-in first version backends: `local`, `webdav`, `ftp`, `ftps`, `sftp`
- Reserved backend module entries: `s3`, `baidu`, `unicom`
- Metadata file for backup records
- Retention cleanup by recent count and age

## Commands

```text
!!wp           show help
!!wp now       create and upload a backup now
!!wp list      list recent backup records
!!wp status    show current status
!!wp clean     apply retention cleanup
!!wp reload    reload config.json
!!wp cn        switch command output to Chinese
!!wp en        switch command output to English
```

Backup sizes in command output are displayed with adaptive units such as `KiB`, `MiB`, and `GiB`.

## Config

The plugin creates `config/walap_upload/config.json` on first load.

Set command output language with `language`:

```json
"language": "en"
```

Allowed values are `en` and `cn`. You can also switch it in game or console with `!!wp en` and `!!wp cn`.

Default upload target is `local`, which copies backups to `./remote_backups` for testing. For netdisk compatibility, use `webdav` first. Baidu Netdisk and China Unicom Netdisk are best connected through Alist/WebDAV in the first version.

`world_dirs` supports exact paths and glob patterns. For servers with different world folder layouts, use patterns such as:

```json
"world_root": "./server",
"world_dirs": ["world*"]
```

This matches directories under `world_root`, such as `world`, `world_nether`, `world_the_end`, `world_survival`, and other folder names beginning with `world`.

Example WebDAV target:

```json
{
  "name": "alist_webdav",
  "type": "webdav",
  "enabled": true,
  "url": "https://example.com/dav/minecraft-backups",
  "username": "user",
  "password": "pass",
  "remote_prefix": "survival/"
}
```

Example FTP target:

```json
{
  "name": "ftp_backup",
  "type": "ftp",
  "enabled": true,
  "host": "ftp.example.com",
  "port": 21,
  "username": "user",
  "password": "pass",
  "remote_prefix": "survival/"
}
```

Example SFTP target:

```json
{
  "name": "backup_server",
  "type": "sftp",
  "enabled": true,
  "host": "backup.example.com",
  "port": 22,
  "username": "root",
  "password": "change-me",
  "base_dir": "/opt/walap-backups",
  "remote_prefix": "survival/"
}
```

## First Version Scope

Implemented now:

- `local`
- `webdav`
- `ftp`
- `ftps`
- `sftp`

Reserved but not implemented yet:

- `s3`
- `baidu`
- `unicom`

This keeps the plugin usable while preserving the module boundary for object storage and direct netdisk API support.