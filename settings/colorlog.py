import logging
import logging.config

from logutils.colorize import ColorizingStreamHandler

class ColorLogHandler(ColorizingStreamHandler):
    def __init__(self, *args, **kwargs):
        super(ColorLogHandler, self).__init__(*args, **kwargs)
        self.level_map = {
            # Provide you custom coloring information here
            logging.DEBUG: (None, 'cyan', False),
            logging.INFO: (None, 'green', False),
            logging.WARNING: (None, 'yellow', False),
            logging.ERROR: (None, 'red', False),
            logging.CRITICAL: ('red', 'white', True),
        }
