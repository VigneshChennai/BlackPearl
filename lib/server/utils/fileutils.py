import asyncio
import pyinotify

class AsyncFileMonitor(pyinotify.Notifier):

    def __init__(self, default_proc_fun, loop=None, read_freq=0,
                 threshold=0, timeout=None, channel_map=None):
        self._wm = pyinotify.WatchManager()
        pyinotify.Notifier.__init__(self, self._wm, default_proc_fun, read_freq,
                          threshold, timeout)
        if not loop:
            loop = asyncio.get_event_loop()
        loop.add_reader(self._fd, self._events_ready)

    def add_watch_path(self, path, rec=False, exclude_filter=pyinotify.ExcludeFilter([])):
        wdd = self._wm.add_watch(path, pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE, rec=rec, 
                            exclude_filter=exclude_filter)

    def _events_ready(self):
        self.read_events()
        self.process_events()
