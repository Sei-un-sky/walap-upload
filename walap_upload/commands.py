from mcdreforged.api.all import *

from .service import format_size


def register_commands(server: PluginServerInterface, service, scheduler):
    builder = SimpleCommandBuilder()
    builder.command('!!wp', lambda source: _help(source, service))
    builder.command('!!wp now', lambda source: _run_backup(source, service, 'manual'))
    builder.command('!!wp list', lambda source: _list_backups(source, service))
    builder.command('!!wp status', lambda source: _status(source, service, scheduler))
    builder.command('!!wp clean', lambda source: _clean(source, service))
    builder.command('!!wp reload', lambda source: _reload(source, service, scheduler))
    builder.command('!!wp cn', lambda source: _set_language(source, service, 'cn'))
    builder.command('!!wp en', lambda source: _set_language(source, service, 'en'))
    builder.register(server)

    server.register_help_message('!!wp', 'Show Walap Upload help')
    server.register_help_message('!!wp now', 'Create and upload a world backup now')
    server.register_help_message('!!wp list', 'List recent backups')
    server.register_help_message('!!wp status', 'Show backup service status')
    server.register_help_message('!!wp clean', 'Apply retention cleanup')


def _run_backup(source: CommandSource, service, trigger: str):
    if service.submit_backup(trigger):
        source.reply(_text(service, 'submitted'))
    else:
        source.reply(_text(service, 'already_running'))


def _list_backups(source: CommandSource, service):
    items = service.metadata.list_records(limit=10)
    if not items:
        source.reply(_text(service, 'no_records'))
        return
    lines = [_text(service, 'recent')]
    for item in items:
        lines.append(f"{item.get('id')} {item.get('status')} {item.get('file_name')} {format_size(int(item.get('size', 0) or 0))}")
    source.reply('\n'.join(lines))


def _status(source: CommandSource, service, scheduler):
    last = service.metadata.last_record()
    last_text = 'none' if last is None else f"{last.get('id')} {last.get('status')}"
    if service.config.language == 'cn':
        source.reply(f'备份运行中={service.is_running()} 定时器={scheduler.is_running()} 最近一次={last_text}')
    else:
        source.reply(f'running={service.is_running()} scheduler={scheduler.is_running()} last={last_text}')


def _clean(source: CommandSource, service):
    result = service.clean_old_backups()
    if service.config.language == 'cn':
        source.reply(f"清理完成，本地删除={result['local_deleted']}，远端删除={result['remote_deleted']}")
    else:
        source.reply(f"cleanup done, local_deleted={result['local_deleted']}, remote_deleted={result['remote_deleted']}")


def _reload(source: CommandSource, service, scheduler):
    service.reload_config()
    scheduler.reload(service.config)
    source.reply(_text(service, 'reloaded'))


def _set_language(source: CommandSource, service, language: str):
    service.config.set_language(language)
    source.reply(_text(service, 'language_cn' if language == 'cn' else 'language_en'))


def _help(source: CommandSource, service):
    if service.config.language == 'cn':
        source.reply('\n'.join([
            'Walap Upload 命令:',
            '!!wp now    立即备份并上传',
            '!!wp list   查看最近备份记录',
            '!!wp status 查看当前状态',
            '!!wp clean  按保留策略清理旧备份',
            '!!wp reload 重载配置',
            '!!wp cn     切换中文',
            '!!wp en     Switch to English',
        ]))
    else:
        source.reply('\n'.join([
            'Walap Upload commands:',
            '!!wp now    create and upload a backup now',
            '!!wp list   list recent backup records',
            '!!wp status show current status',
            '!!wp clean  apply retention cleanup',
            '!!wp reload reload config.json',
            '!!wp cn     切换中文',
            '!!wp en     switch to English',
        ]))


def _text(service, key: str) -> str:
    cn = service.config.language == 'cn'
    messages = {
        'submitted': ('Backup task submitted', '备份任务已提交'),
        'already_running': ('Backup is already running', '已有备份任务正在运行'),
        'no_records': ('No backup records', '没有备份记录'),
        'recent': ('Recent backups:', '最近备份:'),
        'reloaded': ('Walap Upload config reloaded', 'Walap Upload 配置已重载'),
        'language_cn': ('Language switched to Chinese', '已切换为中文'),
        'language_en': ('Language switched to English', 'Switched to English'),
    }
    en_text, cn_text = messages[key]
    return cn_text if cn else en_text