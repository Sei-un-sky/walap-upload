# Installation Guide

This guide installs Walap Upload `v0.3.0` into an existing MCDReforged server.

## Requirements

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- A running Minecraft server managed by MCDReforged
- Python package `paramiko` if you use the `sftp` backend

The plugin does not restore worlds automatically. Restore is manual: download a backup, stop the server, replace the world folders yourself, then start the server.

## Install The Plugin

1. Download `walap_upload-v0.3.0.mcdr` from the release.
2. Put it into your MCDReforged `plugins/` directory.
3. Restart MCDReforged, or run:

```text
!!MCDR plugin load walap_upload
```

4. The plugin creates this config file on first load:

```text
config/walap_upload/config.json
```

If the plugin reports `No module named 'walap_upload'`, the downloaded `.mcdr` archive has an invalid structure. A valid archive must contain `walap_upload/__init__.py`.

## Install Optional Dependency For SFTP

If MCDReforged runs inside a Python virtual environment:

```bash
./venv/bin/python -m pip install paramiko
```

If MCDReforged uses system Python:

```bash
python3 -m pip install paramiko
```

`local`, `webdav`, `ftp`, and `ftps` do not require `paramiko`.

## Basic Config

Default world matching is:

```json
"world_root": "./server",
"world_dirs": ["world*"]
```

This matches world folders under `./server`, such as `world`, `world_nether`, `world_the_end`, and `world_survival`.

For servers where MCDReforged runs directly in the Minecraft server directory, use:

```json
"world_root": ".",
"world_dirs": ["world*"]
```

## SFTP Example

```json
"upload": {
  "enabled": true,
  "mode": "all",
  "retry_count": 3,
  "retry_interval_seconds": 30,
  "targets": [
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
  ]
}
```

## WebDAV Example

Use WebDAV for Alist, NAS, Nextcloud, and compatible netdisk setups:

```json
"upload": {
  "enabled": true,
  "mode": "all",
  "retry_count": 3,
  "retry_interval_seconds": 30,
  "targets": [
    {
      "name": "alist_webdav",
      "type": "webdav",
      "enabled": true,
      "url": "https://example.com/dav/minecraft-backups",
      "username": "user",
      "password": "pass",
      "remote_prefix": "survival/"
    }
  ]
}
```

## Commands

```text
!!wp           show help
!!wp now       create and upload a backup now
!!wp list      list recent backup records
!!wp status    show current status
!!wp clean     apply retention cleanup
!!wp test      test enabled remote storage connections
!!wp reload    reload config.json
!!wp cn        switch command output to Chinese
!!wp en        switch command output to English
```

## Verify Installation

Run:

```text
!!wp
!!wp status
!!wp now
```

After `!!wp now`, check:

- local backup directory from `backup.local_dir`
- remote storage target path
- `config/walap_upload/metadata.json`

Minecraft saving is paused only while the plugin copies a temporary world snapshot. It runs `save-on` immediately after the snapshot is complete, then creates and uploads the archive from that snapshot. The `backup.temp_dir` filesystem must have enough free space for a temporary copy of the configured world directories.