#!/usr/bin/env python

# This file is part of BlackPearl.

# BlackPearl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BlackPearl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
import pyinotify

logger = logging.getLogger(__name__)


class AsyncFileMonitor(pyinotify.Notifier):
    def __init__(self, default_proc_fun, loop=None, read_freq=0,
                 threshold=0, timeout=None, channel_map=None):
        self._wm = pyinotify.WatchManager()
        pyinotify.Notifier.__init__(self, self._wm, default_proc_fun, read_freq,
                                    threshold, timeout)
        if not loop:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.loop.add_reader(self._fd, self._events_ready)
        self.wdd = None
        self.path = None
        self.exclude_filter = None

    def set_watch_path(self, path, rec=False, exclude_filter=pyinotify.ExcludeFilter([])):
        if not self.wdd:
            self.path = path
            self.exclude_filter = exclude_filter
            self.wdd = self._wm.add_watch(path, pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE,
                                          rec=rec,
                                          exclude_filter=exclude_filter)

    def update_watch_path(self, rec=False):
        if self.wdd:
            self._wm.rm_watch(self.wdd.values(), rec=True)
            self.wdd = self._wm.add_watch(self.path,
                                          pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE, rec=rec,
                                          exclude_filter=self.exclude_filter)

    def _events_ready(self):
        self.read_events()
        self.process_events()

    def stop(self):
        self.loop.remove_reader(self._fd)
        pyinotify.Notifier.stop(self)
