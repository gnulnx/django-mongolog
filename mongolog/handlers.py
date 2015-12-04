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
from logging import Handler, StreamHandler, NOTSET
from datetime import datetime
import json

import pymongo 

from mongolog.exceptions import MongoLogError
from mongolog.models import LogRecord

import logging
logger = logging.getLogger('django')


class MongoLogHandler(Handler):
    """
    A handler class which allows logging to use mongo db as the backend
    """
    SIMPLE='simple'
    VERBOSE='verbose'
    record_types = [SIMPLE, VERBOSE]

    def __init__(self, level=NOTSET, connection=None, w=1, j=False, record_type="verbose", time_zone="local"):
        self.connection = connection

        # Choose between verbose and simpel log record types
        self.record_type = record_type
        
        # Used to determine which time setting is used in the simple record_type
        self.time_zone = time_zone

        if not self.connection:
            print("'connection' key not provided in logging config")
            print("Will try to connect with default")

            # Set a defaul connection key
            self.connection = 'mongodb://localhost:27017/'

        self.connect()

        return super(MongoLogHandler, self).__init__(level)

    def __unicode__(self):
        return self.connection

    def __str__(self):
        return self.__unicode__()

    def connect(self):
        major_version = int(pymongo.version.split(".")[0])

        if major_version == 3:
            self.connect_pymongo3()
        elif major_version == 2:
            self.connect_pymongo2()

    def connect_pymongo3(self):
        try:
            self.client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5)
            info = self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as e:
            msg = "Unable to connect to mongo with (%s)" % self.connection
            logger.exception(msg)
            raise pymongo.errors.ServerSelectionTimeoutError(msg)
        
        self.db = self.client.mongolog
        self.collection = self.db.mongolog

    def connect_pymongo2(self):
        # TODO Determine proper try/except logic for pymongo 2.7 driver
        self.client = pymongo.MongoClient(self.connection)
        info = self.client.server_info()
        self.db = self.client.mongolog
        self.collection = self.db.mongolog
    
    def set_record_type(self, rtype):
        """
        Used to set record type on fly...for example during testing
        """
        if rtype not in self.record_types:
            raise ValueError("type must be one of %s" % self.record_types)

        self.record_type = rtype

    def verbose_record(self, record):
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

        return log_record

    def simple_record(self, record):
        log_record = LogRecord({
            # name of the logger
            'name': record.name,
            'thread': record.thread,  # thread number
            'time': datetime.utcnow() if self.time_zone == 'utc' else datetime.now(),
            'process': record.process,  # process number
            'level': record.levelname,
            'msg': record.msg,
            'path': record.pathname,
            'module': record.module,
            'line': record.lineno,
            'func': record.funcName,
            'filename': record.filename,
        })    
        # Add exception info
        if record.exc_info:
            log_record['exception'] = record.exc_text,

        return log_record

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        record = self.process_record(record)
        # Logrecord Attributes: https://docs.python.org/2/library/logging.html#logrecord-attributes
        if self.record_type == "verbose":
            log_record = self.verbose_record(record)
        elif self.record_type == "simple":
            log_record = self.simple_record(record)

        if int(pymongo.version[0]) < 3:
            self.collection.insert(log_record)
        else: 
            self.collection.insert_one(log_record)

    def process_tuple(self, items):
        ret_items = []
        for item in items:
            if isinstance(item, AttributeError):
                item = str(item.message)
            ret_items.append(str(item))
        return ret_items

    def process_record(self, record):
        for k, v in record.__dict__.items():
            if k == 'exc_text' and v:
                v = tuple(v.split("\n"))
            if isinstance(v, tuple):
                v = self.process_tuple(v)

            try:
                test = json.dumps(v)
                record.__dict__[k] = v
            except TypeError as e:
                if "is not JSON serializable" in str(e):
                    logger.exception("Failed to log message(%s) converting to str" % str(e))
                    record.__dict__[k] = str(v)
                else:
                    raise
        return record

    

    
        
