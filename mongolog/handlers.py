#!/usr/bin/env python
from logging import Handler, NOTSET
from pymongo import MongoClient
from datetime import datetime

from mongolog.exceptions import MongoLogError


class MongoLogHandler(Handler):
    """
    A handler class which allows logging to use mongo db as the backend
    """
    def __init__(self, level=NOTSET, connection=None):
        self.connection = connection
        if not self.connection:
            print "'connection' key not provided in logging config"
            print "Will try to connect with default"

            # Set a defaul connection key
            self.connection = 'mongodb://localhost:27017/'

        client = MongoClient(self.connection)
        self.db = client.mongolog

        return super(MongoLogHandler, self).__init__(level)

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        record = self.process_record(record)
        # Logrecord Attributes: https://docs.python.org/2/library/logging.html#logrecord-attributes
        log_record = {
            # name of the logger
            'name': record.name,
            'thread': {
                'num': record.thread,
                'name': record.threadName,
            },
            'time': {
                'utc': datetime.utcnow(),
                'loc': datetime.now(),
            },
            'process': {
                'num': record.process,
                'name': record.processName,
            },
            'level': {
                'name': record.levelname,
                'num': record.levelno,
            },
            'info': {
                'msg': record.getMessage(),
                'path': record.pathname,
                'module': record.module,
                'line': record.lineno,
                'func': record.funcName,
                'filename': record.filename,
            },
        }    
        # Add exception info
        if record.exc_info:
            log_record['exception'] = {
                'info': record.exc_info,
                'trace': record.exc_text,
            }
        self.db.mongolog.insert(log_record)

    def format(self, record):
        raise MongoLogError("format is not defined")

    def process_tuple(self, items):
        ret_items = []
        for item in items:
            if isinstance(item, AttributeError):
                item = unicode(item.message)
            ret_items.append(unicode(item))
        return ret_items

    def process_record(self, record):
        for k, v in record.__dict__.items():
            if k == 'exc_text' and v:
                v = tuple(v.split("\n"))
            if isinstance(v, tuple):
                v = self.process_tuple(v)
            record.__dict__[k] = v
        return record

    

    
        
