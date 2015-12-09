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
from __future__ import print_function
from logging import Handler, NOTSET
from datetime import datetime
import json

import pymongo

from mongolog.models import LogRecord

import logging
logger = logging.getLogger('')


def get_mongolog_handler():
    """
    Return the first MongoLogHander found in the current loggers
    list of handlers
    """
    logger = logging.getLogger('')
    handler = None
    for _handler in logger.handlers:
        if isinstance(_handler, BaseMongoLogHandler):
            handler = _handler
            break
    return handler


class BaseMongoLogHandler(Handler):
    def __init__(self, level=NOTSET, connection=None, w=1, j=False, verbose=None, time_zone="local"):  # noqa
        self.connection = connection

        # Used to determine which time setting is used in the simple record_type
        self.time_zone = time_zone

        # If True will print each log_record to console before writing to mongo
        self.verbose = verbose

        if not self.connection:
            print("'connection' key not provided in logging config")
            print("Will try to connect with default")

            # Set a defaul connection key
            self.connection = u'mongodb://localhost:27017/'

        self.connect()

        return super(BaseMongoLogHandler, self).__init__(level)

    def __unicode__(self):
        return u'%s' % self.connection

    def __str__(self):
        return self.__unicode__()

    def connect(self, test=False):
        major_version = int(pymongo.version.split(".")[0])

        if major_version == 3:
            self.connect_pymongo3(test)
        elif major_version == 2:
            self.connect_pymongo2()

    def connect_pymongo3(self, test=False):
        try:
            if test:
                raise pymongo.errors.ServerSelectionTimeoutError("Just a test")

            self.client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5)
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError:
            msg = "Unable to connect to mongo with (%s)" % self.connection
            logger.exception({'note': 'mongolog', 'msg': msg})
            raise pymongo.errors.ServerSelectionTimeoutError(msg)
        
        self.db = self.client.mongolog
        self.collection = self.db.mongolog

    def connect_pymongo2(self):
        # TODO Determine proper try/except logic for pymongo 2.7 driver
        self.client = pymongo.MongoClient(self.connection)
        self.client.server_info()
        self.db = self.client.mongolog
        self.collection = self.db.mongolog

    def get_collection(self):
        """
        Return the collection being used by MongoLogHandler
        """
        return getattr(self, "collection", None)
    
    def create_log_record(self, record):
        """
        Override in subclasses to change log record formatting.
        See SimpleMongoLogHandler and VerboseMongoLogHandler
        """
        return LogRecord(json.loads(json.dumps(record.__dict__, default=str)))

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        log_record = self.create_log_record(record)
        # log_record = json.loads(json.dumps(log_record, default=str))
        # set this up so you can pass the verbose
        if self.verbose:
            print(json.dumps(log_record, sort_keys=True, indent=4, default=str))

        if int(pymongo.version[0]) < 3:
            self.collection.insert(log_record)
        else: 
            self.collection.insert_one(log_record)
    

class SimpleMongoLogHandler(BaseMongoLogHandler):
    def create_log_record(self, record):
        record = super(SimpleMongoLogHandler, self).create_log_record(record)
        mongolog_record = LogRecord({
            'name': record['name'],
            'thread': record['thread'],
            'time': datetime.utcnow() if self.time_zone == 'utc' else datetime.now(),
            'process': record['process'],
            'level': record['levelname'],
            'msg': record['msg'],
            'path': record['pathname'],
            'module': record['module'],
            'line': record['lineno'],
            'func': record['funcName'],
            'filename': record['filename'],
        })
        # Add exception info
        if record['exc_info']:
            mongolog_record['exception'] = {
                'info': record['exc_info'],
                'trace': record['exc_text'].split("\n") if record['exc_text'] else None,
            }
        return mongolog_record


class VerboseMongoLogHandler(BaseMongoLogHandler):
    def create_log_record(self, record):
        record = super(VerboseMongoLogHandler, self).create_log_record(record) 
        mongolog_record = LogRecord({
            'name': record['name'],
            'thread': {
                'num': record['thread'],
                'name': record['threadName'],
            },
            'time': {
                'utc': datetime.utcnow(),
                'loc': datetime.now(),
            },
            'process': {
                'num': record['process'],
                'name': record['processName'],
            },
            'level': {
                'name': record['levelname'],
                'num': record['levelno'],
            },
            'info': {
                'msg': record['msg'],
                'path': record['pathname'],
                'module': record['module'],
                'line': record['lineno'],
                'func': record['funcName'],
                'filename': record['filename'],
            },
        })    

        if record['exc_info']:
            mongolog_record['exception'] = {
                'info': record['exc_info'],
                'trace': record['exc_text'],
            }

        return mongolog_record