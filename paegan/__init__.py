__import__('pkg_resources').declare_namespace(__name__)

import logging

try:
    PROGRESS=15
    logging.PROGRESS = PROGRESS
    logging.addLevelName(PROGRESS, 'PROGRESS')
    def progress(self, message, *args, **kws):
        if self.isEnabledFor(PROGRESS):
            self._log(PROGRESS, message, args, **kws)
    logging.Logger.progress = progress
except:
    pass
