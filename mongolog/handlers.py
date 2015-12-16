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
import logging
from logging import Handler, NOTSET
from datetime import datetime as dt
import json
import uuid
import pymongo
major_version = int(pymongo.version.split(".")[0])
if major_version >= 3:
    from pymongo.collection import ReturnDocument

from mongolog.models import LogRecord

logger = logging.getLogger('')

uuid_namespace = uuid.UUID('8296424f-28b7-5982-a434-e6ec8ef529b3')


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

        # The write concern
        self.w = w

        # If True block until write operations have been committed to the journal.
        self.j = j

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

        # Make sure the indexes are setup properly
        self.ensure_collections_indexed()

        return super(BaseMongoLogHandler, self).__init__(level)

    def __unicode__(self):
        return u'%s' % self.connection

    def __str__(self):
        return self.__unicode__()

    def connect(self, test=False):

        if major_version == 3:
            self.client = self.connect_pymongo3(test)
        elif major_version == 2:
            self.client = self.connect_pymongo2()

        # The mongolog database
        self.db = self.client.mongolog

        # This is the primary log document collection
        self.mongolog = self.db.mongolog

        # This is the timestamp collection
        self.timestamp = self.db.timestamp

    def connect_pymongo3(self, test=False):

        try:
            if test:
                raise pymongo.errors.ServerSelectionTimeoutError("Just a test")

            self.client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5, w=self.w, j=self.j)
        except pymongo.errors.ServerSelectionTimeoutError:
            msg = "Unable to connect to mongo with (%s)" % self.connection
            # NOTE: Trying to log here ends up with Duplicate Key errors on upsert in emit()
            print(msg)
            raise pymongo.errors.ServerSelectionTimeoutError(msg)
        
        return self.client
        
    def connect_pymongo2(self):
        # TODO Determine proper try/except logic for pymongo 2.7 driver
        self.client = pymongo.MongoClient(self.connection)
        self.client.server_info()
        return self.client

    def get_collection(self):
        """
        Return the collection being used by MongoLogHandler
        """
        return getattr(self, "mongolog", None)
    
    def create_log_record(self, record):
        """
        Convert the python LogRecord to a MongoLog Record.
        Also add a UUID which is a combination of the log message and log level.

        Override in subclasses to change log record formatting.
        See SimpleMongoLogHandler and VerboseMongoLogHandler
        """
        record = LogRecord(json.loads(json.dumps(record.__dict__, default=str)))

        # The UUID is a combination of the record.levelname and the record.msg
        record.update({
            'uuid': uuid.uuid5(
                uuid_namespace, 
                str(record['msg']) + str(record['levelname']) 
            ).hex,
            #'Dates': []
        })
        
        return record

    def ensure_collections_indexed(self):
        """
        Create the indexes if they are not already created
        """
        self.mongolog.create_index([("uuid", 1)], unique=True)
        #self.mongolog.create_index([("dates", 1)])

        self.timestamp.create_index([
            ("mid", 1),
            ("ts", 1)
        ])

    def emit(self, record):
        """ 
        From python:  type(record) == LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        log_record = self.create_log_record(record)

        log_record.get('uuid', ValueError("You must have a uuid in your LogRecord"))
        
        # NOTE: if the user is using django and they have USE_TZ=True in their settings
        # then the timezone displayed will be what is specified in TIME_ZONE
        # For instance if they have TIME_ZONE='UTC' then both dt.now() and dt.utcnow()
        # will be equivalent.
        log_record.update({
            'time': dt.utcnow() if self.time_zone == 'utc' else dt.now(),
            #'dates': [dt.utcnow() if self.time_zone == 'utc' else dt.now()]
        })

        if self.verbose:
            print(json.dumps(log_record, sort_keys=True, indent=4, default=str))

        if int(pymongo.version[0]) < 3:
            self.insert_pymongo_2(log_record)
        else:
            #self.insert_pymongo_3(log_record)
            self.upsert_pymongo_3(log_record)

    def insert_pymongo_2(self, log_record):
        query = {'uuid': log_record['uuid']}

        # remove the old document
        self.mongolog.find_and_modify(query, remove=True)
        
        # insert the new one
        _id = self.mongolog.insert(log_record)

        # Add an entry in the timestamp collection
        self.timestamp.insert({
            'uuid': log_record['uuid'],
            'ts': log_record['time']
        })

    def upsert_pymongo_3(self, log_record):
        query = {'uuid': log_record['uuid']}

        result = self.mongolog.find(query)
        if result.count():
            self.mongolog.update_one(query, {"$push": {'dates': log_record['time']}})
        else:
            self.mongolog.insert_one(log_record)

    def insert_pymongo_3(self, log_record):
        query = {'uuid': log_record['uuid']}
        result = self.mongolog.find_one_and_replace(
            query,
            log_record,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        # Now update the timestamp collection
        # We can do this with a lower write concern than the previous operation since 
        # we can alway's retreive the last datetime from the mongolog collection
        self.timestamp.insert({
            'uuid': log_record['uuid'],
            'ts': log_record['time']
        })


class SimpleMongoLogHandler(BaseMongoLogHandler):
    def create_log_record(self, record):
        record = super(SimpleMongoLogHandler, self).create_log_record(record)
        mongolog_record = LogRecord({
            'name': record['name'],
            'thread': record['thread'],
            'process': record['process'],
            'level': record['levelname'],
            'msg': record['msg'],
            'path': record['pathname'],
            'module': record['module'],
            'line': record['lineno'],
            'func': record['funcName'],
            'filename': record['filename'],
            'uuid': record['uuid']
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
            'uuid': record['uuid']
        })    

        if record['exc_info']:
            mongolog_record['exception'] = {
                'info': record['exc_info'],
                'trace': record['exc_text'],
            }

        return mongolog_record