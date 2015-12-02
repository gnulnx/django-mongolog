#!/usr/bin/env python
"""
    django-mongolog.  Simple Mongo based logger for Django
    Copyright (C) 2015 - John Furr

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from logging import Handler, StreamHandler, NOTSET
from datetime import datetime

import pymongo 

from mongolog.exceptions import MongoLogError
from mongolog.models import LogRecord

import logging
logger = logging.getLogger('django')


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

        self.connect()

        return super(MongoLogHandler, self).__init__(level)

    def connect(self):
        major_version = int(pymongo.version.split(".")[0])

        if major_version == 3:
            self.connect_pymongo3()
        elif major_version == 2:
            self.connect_pymongo2()

    def connect_pymongo3(self):
        try:
            client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5)
            info = client.server_info()
        except ValueError as e: #pymongo.errors.ServerSelectionTimeoutError as e:
            msg = "Unable to connect to mongo with (%s)" % self.connection
            logger.exception(msg)
            raise pymongo.errors.ServerSelectionTimeoutError(msg)
        
        self.db = client.mongolog

    def connect_pymongo2(self):
        # TODO Determine proper try/except logic for pymongo 2.7 driver
        client = pymongo.MongoClient(self.connection)
        info = client.server_info()
        self.db = client.mongolog
        
    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        record = self.process_record(record)
        # Logrecord Attributes: https://docs.python.org/2/library/logging.html#logrecord-attributes
        log_record = LogRecord({
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
                'msg': record.msg,
                'path': record.pathname,
                'module': record.module,
                'line': record.lineno,
                'func': record.funcName,
                'filename': record.filename,
            },
        })    
        # Add exception info
        if record.exc_info:
            log_record['exception'] = {
                'info': record.exc_info,
                'trace': record.exc_text,
            }

        if int(pymongo.version[0]) < 3:
            self.db.mongolog.insert(log_record)
        else: 
            self.db.mongolog.insert_one(log_record)

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

    

    
        
