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
            client = self.connect_pymongo3(test)
        elif major_version == 2:
            client = self.connect_pymongo2()

        # The mongo database
        self.db = self.client.mongolog

        # This is the primary log document collection
        self.mongolog = self.db.mongolog

        # This is the timestamp collection
        self.timestamp = self.db.timestamp

    def connect_pymongo3(self, test=False):

        try:
            if test:
                raise pymongo.errors.ServerSelectionTimeoutError("Just a test")

            self.client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5)
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
        Override in subclasses to change log record formatting.
        See SimpleMongoLogHandler and VerboseMongoLogHandler
        """
        record = LogRecord(json.loads(json.dumps(record.__dict__, default=str)))

        # Makesure we include a uuid
        # The UUID is a combination of the record.levelname and the record.msg
        record.update({
            'uuid':  uuid.uuid5(
                uuid_namespace, 
                str(record['msg']) + str(record['levelname']) 
            ).hex
        })
        # Set variables here before subclasses modify the record format
        # NOTE: self.level is defined as an int() in python 3 so don't know this self.level
        self.level_txt = record['levelname']
        print("self.level.txt(%s)" % self.level_txt)
        self.msg = record['msg']
        print("self.msg(%s)" % self.msg)
        self.uuid = record['uuid']
        print("self.uuid(%s" % self.uuid)
        return record

    def ensure_collections_indexed(self):
        """
        Create the indexes if they are not already created
        """
        self.mongolog.create_index(
            [
                ("level", 1),
                ("uuid", 1)
            ],
            unique=True
        )

        self.timestamp.create_index([
            ("mid", 1),
            ("ts", 1)
        ])

    def emit(self, record):
        """ 
        record = LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        log_record = self.create_log_record(record)
        assert log_record.get('uuid', None) is not None

        # NOTE: if the user is using django and they have USE_TZ=True in their settings
        # then the timezone displayed will be what is specified in TIME_ZONE
        # For instance if they have TIME_ZONE='UTC' then both dt.now() and dt.utcnow()
        # will be equivalent.
        log_record.update({
            'time': dt.utcnow() if self.time_zone == 'utc' else dt.now()
        })

        self.verbose=False
        if self.verbose:
            print(json.dumps(log_record, sort_keys=True, indent=4, default=str))

        if int(pymongo.version[0]) < 3:
            self.insert_pymongo_2(log_record)
        else:
            self.insert_pymongo_3(log_record)

    def insert_pymongo_2(self, log_record):
        query = {'uuid': log_record['uuid']}

        print("query(%s)" % query)
        # TODO This needs to do an upsert now
        result = self.mongolog.find_and_modify(query, remove=True)
        #raise Exception(result)

        print('BEFORE 2')
        for r in self.mongolog.find(query):
            print("r(%s)" % r)
        print("AFTER 2")

        #try:
        _id = self.mongolog.insert(log_record)
        #except:
        #    raise Exception(log_record)

        # Now update the timestamp collection
        self.timestamp.insert({
            'mid': _id,
            'ts': log_record['time']
        })


    def insert_pymongo_3(self, log_record):
        query = {
            'level': self.level_txt,
            'msg': self.msg,
        }
        try:
            result = self.mongolog.find_one_and_replace(
                query,
                log_record,
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
        except pymongo.errors.DuplicateKeyError:
            try:
                result = self.mongolog.find_one_and_replace(
                    query,
                    log_record,
                    upsert=True,
                    return_document=ReturnDocument.AFTER
                )
            except pymongo.errors.DuplicateKeyError:
                # Seems to be strange case that arises out of unit testing.
                # test_connection_error retires the connect with test=True.
                # This ends up raising an exception which does a logger.exception(...) call.
                # That call ends up failing here with a Duplicate Key Error.  The strange thing
                # is the find_one operation here with the same query returns None.
                if not self.mongolog.find_one(query):
                    return
                raise

        # Now update the timestamp collection
        self.timestamp.insert_one({
            'mid': result['_id'],
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