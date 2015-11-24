#!/usr/bin/env python
import logging
import pymongo

# This stuff needs to be moved to settings variables
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client.mongologger

class MongoLoggerHandler(logging.StreamHandler):
    """
    A handler class which allows users mongo db as the backend
    """
    def process_tuple(self, items):
        ret_items = []
        for item in items:
            if type(item) == AttributeError:
                # This is because of exc_info when logger.exception("asdf") is used
                item = item.message
            ret_items.append(str(item))
        return ret_items

    def process_record(self, record):
        for k, v in record.__dict__.items():
            if type(v) == tuple:
                v = self.process_tuple(v)
            record.__dict__[k] = v
        return record

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        record = self.process_record(record)
        try:
            print record.__dict__
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
                'levelname': record.levelname,
                'msecs': record.msecs
            }    
            db.mongologger.insert(log_record)
        except (KeyboardInterrupt, SystemExit):
            raise
