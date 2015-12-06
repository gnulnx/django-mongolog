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
import pprint
pp = pprint.PrettyPrinter(indent=4)

import pymongo 

from mongolog.exceptions import MongoLogError
from mongolog.models import LogRecord

import logging
logger = logging.getLogger('')


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

    @staticmethod
    def handler():
        """
        Return the first MongoLogHander found in the current loggers
        list of handlers
        """
        logger = logging.getLogger('')
        handler = None
        for _handler in logger.handlers:
            if isinstance(_handler, MongoLogHandler):
                handler = _handler
                break
        return handler

    def get_collection(self):
        """
        Return the collection being used by MongoLogHandler
        """
        return getattr(self, "collection", None)

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
            logger.exception({'note': 'mongolog', 'msg': msg})
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
            log_record['exception'] = {
                'info': record.exc_info,
                'trace': record.exc_text,
            }

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

        self.verbose = True
        if self.verbose == True:
            print(json.dumps(log_record, sort_keys=True, indent=4, default=str))

        if int(pymongo.version[0]) < 3:
            self.collection.insert(log_record)
        else: 
            self.collection.insert_one(log_record)
                
    def process_record(self, record):
        # Make sure the entire log message is JSON serializable.
        record.msg = self.ensure_json(record.msg)
        return self.process_record_exception(record)

    def ensure_json(self, value):
        """
        Use json.dumps(...) to ensure that 'value' is in json format.
        The default=str option will attempt to convert any non serializable
        objects/sub objects to a string.

        Once the object has been json serialized we again use json to json.loads
        the json string into a python dictionary.   We do this because pymongo
        uses a slighlyt different serialization when inserting python data
        into mongo and deserialization when pulling it out. 
        """
        return json.loads(json.dumps(value, default=str))


    def process_record_exception(self, record):
        """
        Check for record attributes indicating the logger.exception(...)
        method was called.  If those attrbutes are found ensure that they 
        are converted to JSON serializable formats.  exc_text is also 
        split up based on lines to make for nice stack trace prints inside
        mongo.
        """
        if hasattr(record, "exc_info"):
            record.exc_info = self.ensure_json(record.exc_info)

        if hasattr(record, "exc_text"):
            exc_text = record.exc_text.split("\n") if record.exc_text else None
            record.exc_text = self.ensure_json(exc_text)

        return record

    

        


    

    
        
