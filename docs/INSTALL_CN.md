# 安装教程

本文说明如何把 Walap Upload `v0.3.0` 安装到已有的 MCDReforged 服务端。

## 环境要求

- MCDReforged `>= 2.12.0`
- Python `>= 3.8`
- Minecraft 服务端由 MCDReforged 管理
- 如果使用 `sftp` 后端，需要安装 Python 包 `paramiko`

插件不提供自动回档。需要回档时，请手动下载备份、停止服务端、替换世界目录，然后再启动服务端。

## 安装插件

1. 从 release 下载 `walap_upload-v0.3.0.mcdr`。
2. 放入 MCDReforged 的 `plugins/` 目录。
3. 重启 MCDReforged，或者执行：

```text
!!MCDR plugin load walap_upload
```

4. 插件首次加载时会生成配置文件：

```text
config/walap_upload/config.json
```

如果插件提示 `No module named 'walap_upload'`，说明下载到的 `.mcdr` 包结构不正确。正确的包内必须包含 `walap_upload/__init__.py`。

## 安装 SFTP 依赖

如果 MCDReforged 使用 Python 虚拟环境：

```bash
./venv/bin/python -m pip install paramiko
```

如果 MCDReforged 使用系统 Python：

```bash
python3 -m pip install paramiko
```

`local`、`webdav`、`ftp`、`ftps` 不需要 `paramiko`。

## 基础配置

默认世界匹配配置：

```json
"world_root": "./server",
"world_dirs": ["world*"]
```

这会匹配 `./server` 下面的 `world`、`world_nether`、`world_the_end`、`world_survival` 等目录。

如果 MCDReforged 就运行在 Minecraft 服务端目录里，可以改成：

```json
"world_root": ".",
"world_dirs": ["world*"]
```

## SFTP 示例

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

## WebDAV 示例

WebDAV 适合 Alist、NAS、Nextcloud、坚果云以及其他兼容网盘：

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

## 命令

```text
!!wp           显示帮助
!!wp now       立即备份并上传
!!wp list      查看最近备份记录
!!wp status    查看当前状态
!!wp clean     按保留策略清理旧备份
!!wp test      测试启用的远端存储连接
!!wp reload    重载 config.json
!!wp cn        切换为中文输出
!!wp en        切换为英文输出
```

## 验证安装

执行：

```text
!!wp
!!wp status
!!wp now
```

执行 `!!wp now` 后检查：

- `backup.local_dir` 对应的本地备份目录
- 远端存储目标路径
- `config/walap_upload/metadata.json`

插件只会在复制临时世界快照时短暂关闭世界自动保存。快照复制完成后立即执行 `save-on`，之后才进行压缩和上传，因此大文件压缩、校验和上传期间游戏可以继续保存。`backup.temp_dir` 对应的磁盘需要有足够空间容纳一份临时世界副本。