
import builtins
import inspect

from time import strftime

class Logger:

    NONE=0
    DEBUG=1
    INFO=2
    ERROR=3
    SEVERE=4
    
    def __init__(self, mode):
        self.mode = mode
        self.log_file = None
        self._orignal_print = builtins.print
        
    def initialize(self, log_file):
        self.log_file = log_file
        builtins.print = self._new_print
    
    def _can_print(self, msg):
        if self.mode == Logger.NONE:
            return False
            
        if msg.startswith("DEBUG:"):
            return Logger.DEBUG >= self.mode
        elif msg.startswith("INFO:"):
            return Logger.INFO >= self.mode
        elif msg.startswith("ERROR:"):
            return Logger.ERROR >= self.mode
        elif msg.startswith("SEVERE:"):
            return Logger.SEVERE >= self.mode
        else:
            return True
            
    def _new_print(self, *args, **kwargs):
        args1 = [str(arg) for arg in args]
        if 'file' not in kwargs:
            try:
                msg = kwargs['sep'].join(args1)
            except:
                msg = ''.join(args1)
            if not self._can_print(msg):
                return
            line = []
            line.append('[')
            line.append(strftime("%Y-%m-%d %H:%M:%S"))
            frm = inspect.currentframe()
            line.append("Module: %s" % frm.f_back.f_globals['__name__'])
            line.append("Line: %s ] " % frm.f_back.f_lineno)
            kwargs['file'] = self.log_file
            self._orignal_print(' '.join(line), *args, **kwargs)
        else:
            self._orignal_print(*args, **kwargs)
