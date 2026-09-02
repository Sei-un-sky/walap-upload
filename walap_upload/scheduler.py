import threading
from typing import Optional


class BackupScheduler:
    def __init__(self, server, config, service):
        self.server = server
        self.config = config
        self.service = service
        self._timer: Optional[threading.Timer] = None
        self._running = False

    def start(self) -> None:
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def reload(self, config) -> None:
        self.config = config
        self.stop()
        self.start()

    def is_running(self) -> bool:
        return self._running

    def _schedule_next(self) -> None:
        if not self._running:
            return
        backup_config = self.config.data.get('backup', {})
        if not backup_config.get('enabled', True):
            return
        interval_seconds = max(60, int(float(backup_config.get('interval_hours', 6)) * 3600))
        self._timer = threading.Timer(interval_seconds, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        try:
            self.service.submit_backup('scheduled')
        finally:
            self._schedule_next()