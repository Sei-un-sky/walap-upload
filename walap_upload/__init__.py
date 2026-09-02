try:
    from mcdreforged.api.all import *
except ModuleNotFoundError:
    PluginServerInterface = object

PLUGIN_METADATA = {
    'id': 'walap_upload',
    'version': '0.1.0',
    'name': 'Walap Upload'
}

_service = None
_scheduler = None


def on_load(server: PluginServerInterface, old):
    from .commands import register_commands
    from .config import Config
    from .metadata import MetadataStore
    from .scheduler import BackupScheduler
    from .service import BackupService

    global _service, _scheduler
    config = Config.load(server)
    metadata = MetadataStore(config.metadata_file)
    _service = BackupService(server, config, metadata)
    _scheduler = BackupScheduler(server, config, _service)
    register_commands(server, _service, _scheduler)
    _scheduler.start()
    server.logger.info('Walap Upload loaded')


def on_unload(server: PluginServerInterface):
    global _scheduler
    if _scheduler is not None:
        _scheduler.stop()
    server.logger.info('Walap Upload unloaded')