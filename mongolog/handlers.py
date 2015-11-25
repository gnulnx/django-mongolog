#!/usr/bin/env python
from logging import Handler, NOTSET
from pymongo import MongoClient

from mongolog.exceptions import MongoLoggerException


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
        self.db = client.mongologger

        return super(MongoLogHandler, self).__init__(level)

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        record = self.process_record(record)
        
        log_record = {
            'threadName': record.threadName,
            'name': record.name,
            'thread': record.thread,
            'created': record.created,
            'process': record.process,
            'processName': record.processName,
            'args': record.args,  # tuple
            'module': record.module,
            'filename': record.filename,
            'levelno': record.levelno,
            'exc_text': record.exc_text,
            'pathname': record.pathname,
            'lineno': record.lineno,
            'msg': record.msg,
            'exc_info': record.exc_info,
            'message': record.message,
            'funcName': record.funcName,
            'relativeCreated': record.relativeCreated,
            'level': record.levelname,
            'msecs': record.msecs
        }    
        self.db.mongologger.insert(log_record)

    def format(self, record):
        raise MongoLoggerException("format is not defined")

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

    

    
        
