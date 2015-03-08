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

import builtins
import inspect

from time import strftime


class Logger:
    NONE = 0
    DEBUG = 1
    FINER = 2
    FINE = 3
    INFO = 4
    WARNING = 5
    ERROR = 6
    SEVERE = 7

    def __init__(self, mode):
        self.mode = mode
        self.log_file = None
        self._original_print = builtins.print
        self.disabled_list = []

    def disable_for_module(self, module_path):
        self.disabled_list.append(module_path)

    def initialize(self):
        builtins.print = self._new_print

    def _can_print(self, msg):
        if self.mode == Logger.NONE:
            return False

        if msg.startswith("DEBUG:"):
            return Logger.DEBUG >= self.mode
        elif msg.startswith("FINER:"):
            return Logger.FINER >= self.mode
        elif msg.startswith("FINE:"):
            return Logger.FINE >= self.mode
        elif msg.startswith("INFO:"):
            return Logger.INFO >= self.mode
        elif msg.startswith("WARNING:"):
            return Logger.WARNING >= self.mode
        elif msg.startswith("ERROR:"):
            return Logger.ERROR >= self.mode
        elif msg.startswith("SEVERE:"):
            return Logger.SEVERE >= self.mode
        else:
            raise ValueError("Not a log")

    def _new_print(self, *args, **kwargs):
        args1 = [str(arg) for arg in args]
        if 'file' not in kwargs:
            try:
                msg = kwargs['sep'].join(args1)
            except:
                msg = ''.join(args1)
            try:
                if not self._can_print(msg):
                    return
                just_a_print = False
            except ValueError:
                just_a_print = True

            frm = inspect.currentframe()
            from_module = frm.f_back.f_globals['__name__']

            if not just_a_print:
                for mod in self.disabled_list:
                    if from_module.startswith(mod):
                        return

            line = ['[', strftime("%Y-%m-%d %H:%M:%S"), "Module:", from_module,
                    "Line: %s" % frm.f_back.f_lineno, "] "]
            # kwargs['file'] = self.log_file
            self._original_print(' '.join(line), *args, **kwargs)
        else:
            self._original_print(*args, **kwargs)
