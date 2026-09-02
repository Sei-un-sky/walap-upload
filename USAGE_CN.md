# 使用文档

本文说明 Walap Upload 的使用方式，并解释每个用户可配置参数的作用。

Walap Upload 在 MCDReforged 数据目录下使用两个文件：

- `config/walap_upload/config.json`：主配置文件。用户需要编辑的是这个文件。
- `config/walap_upload/metadata.json`：插件自动生成的备份记录索引。除非手动修复记录，否则不要编辑。

修改 `config.json` 后，在 MCDR 控制台或游戏内执行 `!!wp reload`，也可以重启 MCDReforged。

## 命令

```text
!!wp           显示帮助
!!wp now       立即创建并上传备份
!!wp list      查看最近备份记录
!!wp status    查看备份任务和定时器状态
!!wp clean     立即执行保留策略清理
!!wp reload    重载 config/walap_upload/config.json
!!wp cn        切换命令输出为中文
!!wp en        切换命令输出为英文
```

同一时间只能运行一个备份任务。如果备份正在运行，再执行 `!!wp now` 会提示已有任务正在运行。

## 默认配置

```json
{
  "server_name": "survival",
  "language": "en",
  "world_root": "./server",
  "world_dirs": ["world*"],
  "backup": {
    "enabled": true,
    "interval_hours": 6,
    "format": "zip",
    "temp_dir": "./backup_tmp",
    "local_dir": "./backups",
    "keep_local_after_upload": true,
    "calculate_sha256": true,
    "save_commands": true
  },
  "upload": {
    "enabled": true,
    "mode": "all",
    "retry_count": 3,
    "retry_interval_seconds": 30,
    "targets": [
      {
        "name": "local_test",
        "type": "local",
        "enabled": true,
        "directory": "./remote_backups",
        "remote_prefix": "survival/"
      }
    ]
  },
  "retention": {
    "enabled": true,
    "keep_last": 10,
    "keep_days": 30,
    "delete_local": true,
    "delete_remote": false
  }
}
```

## 顶层参数

`server_name`

服务器名称，会写入备份文件名和 metadata 记录。生成的备份文件名格式如下：

```text
<server_name>_full_<日期>_<时间>_<触发来源>.zip
```

例如：`survival_full_2026-09-03_03-38-32_scheduled.zip`。

`language`

命令输出语言。`en` 表示英文，`cn` 表示中文。`zh`、`zh_cn` 也会被内部转换为中文。也可以用 `!!wp en` 或 `!!wp cn` 修改，命令会把新语言写回 `config.json`。

`world_root`

世界目录的基准目录，用来解析 `world_dirs` 里的相对路径。相对路径以 MCDR 工作目录为起点解析，也支持绝对路径。

常见配置：

```json
"world_root": "./server"
```

适合 Minecraft 服务端文件放在 MCDR 的 `server` 目录下的情况。

```json
"world_root": "."
```

适合 MCDReforged 直接运行在 Minecraft 服务端目录里的情况。

`world_dirs`

需要打包的世界目录列表。每一项可以是精确目录名，也可以是 glob 通配符。相对路径会在 `world_root` 下匹配，绝对路径会按原样使用。

示例：

```json
"world_dirs": ["world"]
```

只备份 `world`。

```json
"world_dirs": ["world*"]
```

备份 `world`、`world_nether`、`world_the_end`、`world_survival` 等以 `world` 开头的目录。

```json
"world_dirs": ["world", "world_nether", "world_the_end"]
```

明确备份原版常见的三个世界目录。

如果没有任何目录匹配成功，备份会失败，并报错 `No world directories matched config world_dirs`。

## backup

`backup.enabled`

控制定时自动备份。`true` 启用定时器，`false` 禁用定时自动备份。手动命令 `!!wp now` 仍然可以提交备份任务，因为它直接调用备份服务。

`backup.interval_hours`

定时备份间隔，单位是小时。支持小数，因为定时器会用 `float` 把小时转换成秒。

示例：

```json
"interval_hours": 6
```

每 6 小时备份一次。

```json
"interval_hours": 0.5
```

每 30 分钟备份一次。实际最小间隔是 60 秒。

`backup.format`

归档格式配置。`v0.1.0` 的实际实现会创建 zip 压缩包，所以请保持为 `zip`。

`backup.temp_dir`

为备份操作预留的临时工作目录。相对路径同样以 MCDR 工作目录为起点解析。在 `v0.1.0` 中，zip 创建主要直接写入 `local_dir`，但保留独立临时目录配置是为了兼容后续归档实现。

`backup.local_dir`

本地备份 zip 文件的输出目录。相对路径以 MCDR 工作目录为起点解析。插件会在需要时创建该目录。

`backup.keep_local_after_upload`

表达“上传后是否保留本地备份”的用户意图，并为后续行为保留配置位。`v0.1.0` 中，本地旧备份删除主要由备份完成后的 `retention` 部分控制，尤其是 `retention.delete_local`。

`backup.calculate_sha256`

为 `true` 时，插件会计算压缩包的 SHA-256，并写入 `metadata.json`。这可用于校验备份完整性。对于很大的备份，计算哈希会在压缩包生成后增加一次额外磁盘读取时间。

`backup.save_commands`

为 `true` 时，插件会在打包前后执行 Minecraft 存档命令：

```text
save-off
save-all flush
创建 zip 压缩包
save-on
```

上传会在 `save-on` 之后开始，所以世界保存只会在创建压缩包期间暂停。只有在服务端环境不支持这些命令，或者你明确想自己管理保存流程时，才建议设为 `false`。

## upload

`upload.enabled`

上传总开关。`true` 表示把压缩包上传到已启用的目标。`false` 表示只保留本地压缩包，并记录空的上传结果。

`upload.mode`

上传模式配置。默认值是 `all`。在 `v0.1.0` 中，上传器会把备份发送到所有启用的目标，不会根据该字段改变行为，所以保持为 `all` 即可。

`upload.retry_count`

每个上传目标的最大尝试次数。小于 1 的值会按 1 次处理。

`upload.retry_interval_seconds`

同一个上传目标失败后，下次重试前等待的秒数。

`upload.targets`

上传目标对象列表。每个启用的目标都会独立收到备份。只要有任意目标失败，最终备份状态会变成 `partial_failed`。

## 通用上传目标参数

这些字段适用于所有目标类型。

`name`

目标名称。它会作为 `metadata.json` 中上传结果的 key。建议保持稳定，不要随意改名；如果改名，旧记录里的远端备份可能无法被保留策略删除，因为 metadata 记录的是旧名称。

`type`

后端类型。`v0.1.0` 已实现：

- `local`
- `webdav`
- `ftp`
- `ftps`
- `sftp`

已预留但未实现：`s3`、`baidu`、`baidu_netdisk`、`unicom`、`china_unicom_netdisk`。这些占位类型不能用于真实上传。

`enabled`

该目标是否启用。禁用的目标会在上传和远端删除时被跳过。

`remote_prefix`

远端路径前缀，会放在备份文件名前面。插件内部会去掉开头和结尾的斜杠。

示例：

```json
"remote_prefix": "survival/"
```

会得到这样的远端路径：

```text
survival/survival_full_2026-09-03_03-38-32_scheduled.zip
```

可以用不同前缀区分不同服务器、周目或环境。

## local 目标

把备份复制到另一个本地目录。适合测试，也适合复制到已挂载的磁盘。

```json
{
  "name": "local_test",
  "type": "local",
  "enabled": true,
  "directory": "./remote_backups",
  "remote_prefix": "survival/"
}
```

`directory`

复制备份文件的本地基础目录。最终路径是：

```text
<directory>/<remote_prefix>/<file_name>
```

## WebDAV 目标

适合 Alist、NAS、Nextcloud 以及兼容 WebDAV 的网盘。

```json
{
  "name": "alist_webdav",
  "type": "webdav",
  "enabled": true,
  "url": "https://example.com/dav/minecraft-backups",
  "username": "user",
  "password": "pass",
  "timeout": 120,
  "remote_prefix": "survival/"
}
```

`url`

WebDAV 基础地址。插件会把 `remote_prefix` 和备份文件名追加到这个 URL 路径后面。

`username`

WebDAV 用户名。只有在你的 WebDAV 端点允许匿名写入时才可以留空。

`password`

WebDAV 密码、应用密码或 token，具体取决于服务商。

`timeout`

HTTP 连接超时时间，单位秒。默认值是 `120`。

上传前，插件会用 WebDAV `MKCOL` 创建缺失的远端目录。

## FTP / FTPS 目标

`ftp` 表示普通 FTP，`ftps` 表示 FTP over TLS。

```json
{
  "name": "ftp_backup",
  "type": "ftp",
  "enabled": true,
  "host": "ftp.example.com",
  "port": 21,
  "username": "user",
  "password": "pass",
  "timeout": 60,
  "remote_prefix": "survival/"
}
```

`host`

FTP 服务器域名或 IP 地址。

`port`

FTP 服务器端口。如果省略，`ftp` 默认是 `21`，`ftps` 默认是 `990`。

`username`

FTP 登录用户名。

`password`

FTP 登录密码。

`timeout`

连接超时时间，单位秒。默认值是 `60`。

上传前，插件会创建缺失的远端目录。

## SFTP 目标

SFTP 需要在 MCDReforged 使用的同一个 Python 环境中安装 `paramiko`。

```json
{
  "name": "backup_server",
  "type": "sftp",
  "enabled": true,
  "host": "backup.example.com",
  "port": 22,
  "username": "root",
  "password": "change-me",
  "key_filename": null,
  "base_dir": "/opt/walap-backups",
  "timeout": 60,
  "banner_timeout": 60,
  "auth_timeout": 60,
  "remote_prefix": "survival/"
}
```

`host`

SFTP 服务器域名或 IP 地址。

`port`

SSH 端口。默认值是 `22`。

`username`

SSH 用户名。

`password`

SSH 密码。如果使用 `key_filename` 且密钥不需要密码，这里可以留空。

`key_filename`

SSH 私钥文件路径。该字段可选。建议使用绝对路径。

`base_dir`

SFTP 服务器上的基础目录。最终远端路径是：

```text
<base_dir>/<remote_prefix>/<file_name>
```

如果 `base_dir` 为空，插件会相对 SFTP 登录目录上传。

`timeout`

TCP 连接超时时间，单位秒。默认值是 `60`。

`banner_timeout`

SSH banner 超时时间，单位秒。默认值是 `60`。

`auth_timeout`

SSH 认证超时时间，单位秒。默认值是 `60`。

上传前，插件会创建缺失的远端目录。

## retention

保留策略会在每次备份完成后自动运行，也可以用 `!!wp clean` 手动运行。

`retention.enabled`

清理总开关。`true` 启用清理，`false` 表示保留策略不会修改 metadata 记录或删除文件。

`retention.keep_last`

至少保留最新的多少条备份记录。例如 `10` 表示无论这些备份是否超过保留天数，都保留最新 10 个备份。

`retention.keep_days`

保留最近多少天内创建的备份。只有同时满足“不在最新 `keep_last` 条记录里”并且“早于 `keep_days` 天”的备份，才会被选中清理。

`retention.delete_local`

为 `true` 时，清理会删除 metadata 中记录的过期本地 zip 文件。

`retention.delete_remote`

为 `true` 时，清理也会删除已成功上传的过期远端备份。远端删除依赖 metadata 中保存的目标名称，所以请保持上传目标的 `name` 稳定。

保守默认值：

```json
"delete_remote": false
```

这样可以避免用户没有明确开启时误删远端备份。

## metadata.json

`metadata.json` 由插件生成，备份记录保存在 `backups` 列表里。每条记录可能包含：

- `id`：基于创建时间生成的备份 id。
- `server_name`：配置中的服务器名称。
- `created_at`：备份创建时间。
- `trigger`：触发来源，`manual` 或 `scheduled`。
- `file_name`：压缩包文件名。
- `local_path`：本地压缩包路径。
- `status`：`running`、`archived`、`uploaded`、`partial_failed` 或 `failed`。
- `world_dirs`：本次打包的世界目录。
- `size`：压缩包大小，单位字节。
- `sha256`：启用哈希计算时记录的 SHA-256。
- `upload_results`：每个上传目标的上传状态和远端路径。
- `retention_deleted`、`local_deleted`、`remote_deleted_count`：保留策略清理结果字段。

`!!wp list`、`!!wp status` 和保留策略清理都依赖这个文件。

## 常用配置

每 3 小时自动备份一次：

```json
"backup": {
  "enabled": true,
  "interval_hours": 3
}
```

只保留本地文件，不上传：

```json
"upload": {
  "enabled": false
}
```

保留最新 20 个备份，并保留最近 14 天内的备份：

```json
"retention": {
  "enabled": true,
  "keep_last": 20,
  "keep_days": 14,
  "delete_local": true,
  "delete_remote": false
}
```

同时上传到 WebDAV 和 SFTP：

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
    },
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

## 运维注意事项

- `config/walap_upload/config.json` 可能包含存储密码，请妥善保护。
- 新增上传目标后，先用 `!!wp now` 测试，再检查 `metadata.json` 里的上传结果。
- 用 `!!wp status` 查看定时器是否正在运行。
- 修改保留策略后，如果想立即清理，执行 `!!wp clean`。
- 回档需要手动完成：下载备份，停止 Minecraft 服务端，替换世界目录，再启动服务端。