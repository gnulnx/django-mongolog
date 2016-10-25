# -*- coding: utf-8 -*-
# !/usr/bin/env python
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
import sys
try:
    import cStringIO
except: ImportError:
    from io import io.BytesIO as cStringIO

import traceback
import json
import uuid
import pymongo
import requests
pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument

from mongolog.models import LogRecord
from mongolog.exceptions import MissingConnectionError

logger = logging.getLogger('')
console = logging.getLogger('mongolog-int')

uuid_namespace = uuid.UUID('8296424f-28b7-5982-a434-e6ec8ef529b3')


# TODO Move to mongolog.models.Mongolog
def get_mongolog_handler(logger_name=None, show_logger_names=False):
    """
    Return the first MongoLogHander found in the list of defined loggers.
    NOTE: If more than one is defined, only the first one is used.
    """
    if logger_name:
        logger_names = [logger_name]
    else:
        logger_names = [''] + list(logging.Logger.manager.loggerDict)

    if show_logger_names:
        console.info("get_mongolog_handler(): Logger_names: %s", json.dumps(logger_names, indent=4, sort_keys=True, default=str))

    for name in logger_names:
        logger = logging.getLogger(name)
        handler = None
        for _handler in logger.handlers:
            if isinstance(_handler, BaseMongoLogHandler):
                handler = _handler
                break
        if handler:
            console.debug("found handler: %s", handler)
            break

    if not handler:
        raise ValueError("No BaseMongoLogHandler could be found.  Did you add on to youy logging config?")
    return handler


# Copied directly from python Formatter class
def formatException(ei):
    """
    Format and return the specified exception information as a string.

    This default implementation just uses
    traceback.print_exception()
    """
    sio = cStringIO.StringIO()
    traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


class BaseMongoLogHandler(Handler):

    REFERENCE = 'reference'
    EMBEDDED = 'embedded'

    def __init__(self, level=NOTSET, connection=None, w=1, j=False, verbose=None, time_zone="local", record_type="embedded", max_keep=25, *args, **kwargs):  # noqa
        super(BaseMongoLogHandler, self).__init__(level)
        self.connection = connection

        valid_record_types = [self.REFERENCE, self.EMBEDDED]
        if record_type not in valid_record_types:
            raise ValueError("record_type myst be one of %s" % valid_record_types)

        # The type of document we store
        self.record_type = record_type

        # number of dates to keep in embedded document
        self.max_keep = max_keep

        # The write concern
        self.w = w

        # If True block until write operations have been committed to the journal.
        self.j = j

        # Used to determine which time setting is used in the simple record_type
        self.time_zone = time_zone

        # If True will print each log_record to console before writing to mongo
        self.verbose = verbose

        if self.connection:
            self.connect()

            # Make sure the indexes are setup properly
            try:
                self.ensure_collections_indexed()
            except pymongo.errors.ServerSelectionTimeoutError:
                pass
        else:
            console.error("\n----------- Connection Error ------------")
            console.error("Hanlder(%s) missing 'connection' key", type(self))
            console.error("%s", json.dumps(self.__dict__, indent=4, sort_keys=True, default=str))
            console.error("------------------------------------------\n")
            raise MissingConnectionError("Missing 'connection' key")

    def __unicode__(self):
        return u'%s' % self.connection

    def __str__(self):
        return self.__unicode__()

    def connect(self, test=False):

        if pymongo_version == 3:
            self.client = self.connect_pymongo3(test)
        elif pymongo_version == 2:
            self.client = self.connect_pymongo2()

        # The mongolog database
        self.db = self.client.mongolog

        # This is the primary log document collection
        self.mongolog = self.db.mongolog

        # This is the timestamp collection
        self.timestamp = self.db.timestamp

    def get_db(self):
        """
        Return a handler to the database handler
        """
        return getattr(self, "db", None)

    def get_timestamp_collection(self):
        return getattr(self, "timestamp", None)

    def get_collection(self):
        """
        Return the collection being used by MongoLogHandler
        """
        return getattr(self, "mongolog", None)

    def connect_pymongo3(self, test=False):

        try:
            if test:
                raise pymongo.errors.ServerSelectionTimeoutError("Just a test")

            if self.w == 0:
                # if w=0 you can't have other options
                self.client = pymongo.MongoClient(self.connection, serverSelectionTimeoutMS=5, w=self.w)
            else:
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

    def new_key(self, old_key):
        """
        Repalce . and $ with Unicode full width equivalents
        """
        if "." in old_key:
            return old_key.replace(u".", u"．")
        elif "$" in old_key:
            return old_key.replace(u"$", u"＄")
        else:
            return old_key

    def check_keys(self, record):
        """
        Check for . and $ in two levels of keys below msg.
        TODO:   Make this a recursive function that looks for these keys
                n levels deep
        """
        if not isinstance(record['msg'], dict):
            return record

        for k, v in record['msg'].items():
            record['msg'][self.new_key(k)] = record['msg'].pop(k)

            if isinstance(v, dict):
                for old_key in record['msg'][k].keys():
                    record['msg'][k][self.new_key(old_key)] = record['msg'][k].pop(old_key)

        return record

    def create_log_record(self, record):
        """
        Convert the python LogRecord to a MongoLog Record.
        Also add a UUID which is a combination of the log message and log level.

        Override in subclasses to change log record formatting.
        See SimpleMongoLogHandler and VerboseMongoLogHandler
        """
        # This is still a python LogRecord Object that we are manipulating
        if record.exc_info:
            record.exc_text = formatException(record.exc_info)

        record = LogRecord(json.loads(json.dumps(record.__dict__, default=str)))
        if "mongolog.management.commands" in record['name']:
            return {'uuid': 'none', 'time': 'none', 'level': 'MONGOLOG-INTERNAL'}
        record = self.check_keys(record)

        # The UUID is a combination of the record.levelname and the record.msg
        if sys.version_info.major >= 3:
            uuid_key = str(record['msg']) + str(record['levelname'])
        else:
            uuid_key = (unicode(record['msg']) + unicode(record['levelname'])).encode('utf-8', 'replace')

        record.update({
            'uuid': uuid.uuid5(uuid_namespace, uuid_key).hex,
            # NOTE: if the user is using django and they have USE_TZ=True in their settings
            # then the timezone displayed will be what is specified in TIME_ZONE
            # For instance if they have TIME_ZONE='UTC' then both dt.now() and dt.utcnow()
            # will be equivalent.
            'time': dt.utcnow() if self.time_zone == 'utc' else dt.now(),
        })

        # If we are using an embedded document type
        # we need to create the dates array
        if self.record_type == self.EMBEDDED:
            record['dates'] = [record['time']]

        return record

    def ensure_collections_indexed(self):
        """
        Create the indexes if they are not already created
        """
        self.mongolog.create_index([("uuid", 1)], unique=True)
        self.mongolog.create_index([("dates", 1)])
        self.mongolog.create_index([("counter", 1)])

        self.timestamp.create_index([
            ("uuid", 1),
            ("ts", 1)
        ])

    def emit(self, record):
        """
        From python:  type(record) == LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        log_record = self.create_log_record(record)

        # TODO move this to a validate log_record method and add more validation
        log_record.get('uuid', ValueError("You must have a uuid in your LogRecord"))

        if self.verbose:
            print(json.dumps(log_record, sort_keys=True, indent=4, default=str))

        if self.record_type == self.EMBEDDED:
            self.insert_embedded(log_record)

        elif self.record_type == self.REFERENCE:
            if pymongo_version == 2:
                self.reference_log_pymongo_2(log_record)

            elif pymongo_version == 3:
                self.reference_log_pymongo_3(log_record)

    def insert_embedded(self, log_record):
        """
        Insert an embedded document.  Embedded documents have a 'counter'
        variable that increments each time the document is seen.  The 'date'
        array is capped at the last 'max_keep'
        """
        query = {'uuid': log_record['uuid']}
        result = self.mongolog.find(query)
        if result.count() == 0:

            # First time this record has been seen add a created field and insert it
            log_record['created'] = log_record.pop('time')
            log_record['counter'] = 1
            if pymongo_version == 2:
                self.mongolog.insert(log_record)
            elif pymongo_version == 3:
                self.mongolog.insert_one(log_record)
        else:
            # record has been seen before so we update the counter and push/pop
            # the log record time.  We keep the 'n' latest log record
            update = {
                "$push": {
                    'dates': {
                        '$each': [log_record['time']],
                        "$slice": -self.max_keep  # only keep the last n entries
                    }
                },
                # Keep a counter of the number of times we see this record
                "$inc": {'counter': 1}
            }

            if pymongo_version == 2:
                self.mongolog.update(query, update)
            elif pymongo_version == 3:
                self.mongolog.update_one(query, update)

    def reference_log_pymongo_2(self, log_record):
        query = {'uuid': log_record['uuid']}

        # remove the old document
        self.mongolog.find_and_modify(query, remove=True)

        # insert the new one
        self.mongolog.insert(log_record)

        # Add an entry in the timestamp collection
        self.timestamp.insert({
            'uuid': log_record['uuid'],
            'ts': log_record['time']
        })

    def reference_log_pymongo_3(self, log_record):
        query = {'uuid': log_record['uuid']}
        self.mongolog.find_one_and_replace(
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
        if record['uuid'] == 'none':
            return record
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
            'uuid': record['uuid'],
            'time': record['time'],
        })

        if record.get('dates'):
            mongolog_record['dates'] = record['dates']

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
            'uuid': record['uuid'],
            'time': record['time'],
        })

        if record['exc_info']:
            mongolog_record['exception'] = {
                'info': record['exc_info'],
                'trace': record['exc_text'],
            }

        return mongolog_record


class HttpLogHandler(SimpleMongoLogHandler):
    def __init__(self, level=NOTSET, client_auth='', timeout=3, verbose=False, time_zone="local", *args, **kwargs):
        # Make sure there is a trailing slash or reqests 2.8.1 will try a GET instead of POST
        self.client_auth = client_auth if client_auth.endswith('/') else "%s/" % client_auth

        self.timeout = timeout

        # Used to determine which time setting is used in the simple record_type
        self.time_zone = time_zone

        # Intentionally hard coded in HttpLogHandler
        self.record_type = 'reference'

        # If True will print each log_record to console before writing to mongo
        self.verbose = verbose

        # Don't call super here.  We don't want to call BaseMongoLogHandler.__init__ here.
        # But we still need this to be a python  Handler subclass with SimpleMongoLogger.create_log_record
        Handler.__init__(self, level=level)

    def __unicode__(self):
        return u'%s' % self.client_auth

    def emit(self, record):
        """
        From python:  type(record) == LogRecord
        https://github.com/certik/python-2.7/blob/master/Lib/logging/__init__.py#L230
        """
        log_record = self.create_log_record(record)

        # TODO move this to a validate log_record method and add more validation
        log_record.get('uuid', ValueError("You must have a uuid in your LogRecord"))
        if self.verbose:
            print("Inserting", json.dumps(log_record, sort_keys=True, indent=4, default=str))

        customer_id = self.client_auth.split("/")[-2]
        log_record['customer_id'] = customer_id

        r = requests.post(self.client_auth, json=json.dumps(log_record, default=str), timeout=self.timeout, proxies={'http':''})  # noqa
        # uncomment to debug
        try:
            print("Response:", json.dumps(r.json(), indent=4, sort_keys=True, default=str))
        except ValueError as e:
            if "No JSON object could be decoded" in str(e):
                print("log write failed: ", r)
