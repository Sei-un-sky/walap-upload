# Walap Upload

MCDReforged 自动世界备份插件。

`0.1.0` 版本只做一件事：把完整世界目录打包成 zip，然后上传到远端存储。插件不提供自动回档，也不会自动覆盖世界目录。需要回档时，管理员手动下载备份、停服、替换存档。

## 功能

- 手动命令：`!!wp now`
- 输入 `!!wp` 显示帮助
- 支持 `!!wp cn` / `!!wp en` 切换命令输出语言
- 按间隔自动备份
- 把完整世界目录打成一个 zip
- 打包前后执行存档命令：`save-off`、`save-all flush`、打包、`save-on`
- `save-on` 之后才开始上传，所以上传大文件时游戏可以继续正常保存
- 上传后端独立模块化
- 第一版已实现：`local`、`webdav`、`ftp`、`ftps`、`sftp`
- 预留：`s3`、`baidu`、`unicom`
- 记录 metadata 备份索引
- 按保留数量和保留天数清理旧备份
- 命令输出中的备份大小会自动显示为 `KiB`、`MiB`、`GiB`

## 命令

```text
!!wp           显示帮助
!!wp now       立即备份并上传
!!wp list      查看最近备份记录
!!wp status    查看当前状态
!!wp clean     按保留策略清理旧备份
!!wp reload    重载 config.json
!!wp cn        切换为中文输出
!!wp en        切换为英文输出
```

## 配置

插件首次加载时会生成：

```text
config/walap_upload/config.json
```

语言配置：

```json
"language": "cn"
```

可选值：`cn`、`en`。也可以直接用 `!!wp cn` 和 `!!wp en` 切换。

默认上传目标是 `local`，会把备份复制到 `./remote_backups`，适合测试。正式使用网盘时，优先建议用 `webdav`，例如 Alist、NAS、Nextcloud、坚果云等。百度网盘、联通云盘第一版建议通过 Alist/WebDAV 接入。

`world_dirs` 支持精确路径和通配符。不同服务端、整合包的世界目录格式不同，可以这样配置：

```json
"world_root": "./server",
"world_dirs": ["world*"]
```

这会匹配 `world_root` 目录下的 `world`、`world_nether`、`world_the_end`、`world_survival` 等所有以 `world` 开头的目录。

WebDAV 示例：

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

SFTP 示例：

```json
{
  "name": "backup_server",
  "type": "sftp",
  "enabled": true,
  "host": "192.168.10.23",
  "port": 22,
  "username": "root",
  "password": "change-me",
  "base_dir": "/opt/walap-backups",
  "remote_prefix": "survival/"
}
```

## 当前范围

已实现：

- `local`
- `webdav`
- `ftp`
- `ftps`
- `sftp`

预留但未实现：

- `s3`
- `baidu`
- `unicom`

这样第一版可以先稳定使用，同时保留对象存储和网盘直连 API 的模块边界。