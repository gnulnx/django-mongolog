# -*- coding: utf-8 -*-
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
import unittest
import logging
from logging import config  # noqa
import os
import sys
import subprocess
import time
import json
from unittest import skipIf
from requests.exceptions import ConnectionError

# Different imports for python2/3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO  # noqa: F401

import pymongo
pymongo_major_version = int(pymongo.version.split(".")[0])

from mongolog.handlers import SimpleMongoLogHandler
from mongolog.models import Mongolog, get_mongolog_handler

import django
django_version = django.VERSION[0]

from django.core.management import call_command
from django.test import TestCase
from django.test import Client

if django_version < 2:
    from django.core.urlresolvers import reverse
else:
    from django.urls import reverse

from django.conf import settings
LOGGING = settings.LOGGING
console = logging.getLogger("console")

console.info(
    "Available LOGGERS(%s)" % json.dumps(
        logging.Logger.manager.loggerDict, indent=4, sort_keys=True, default=str))


"""
    All log tests should log a dictionary with a 'test' key
    logger.info({
        'test': True,
        'msg': 'special message'
    })

    This key will allow us to easily clean test entries out of the
    database.

    NOTE: You can add any other key you want for testing purposes
"""
TEST_MSG = {
    'test': True,  # String so we can remove test entries
    'test class': 'TestBaseMongoLogHandler',
    'Life': {
        'Domain': {
            'Bacteria': [
                {
                    'name': ValueError,
                    'description': 'Just a bad description',
                    'unicode_test': 'ऄࢩ ࢩ ࢩǢ',
                }
            ],
            'Archaea': [],
            'Eukaryota': [
                {
                    'name': 'Excavata',
                    'description': 'Various flagellate protozoa',
                },
                {
                    'name': 'Amoebozoa',
                    'descritpion': 'most lobose amoeboids and slime moulds',
                },
                {
                    'name': 'Opisthokonta',
                    'description': 'animals, fungi, choanoflagellates, etc.',
                },
                {
                    'name': 'Rhizaria',
                    'description': 'Foraminifera, Radiolaria, and various other amoeboid protozoa'
                },
                {
                    'name': 'Chromalveolata',
                    'description': 'Stramenopiles (Brown Algae, Diatoms etc.)'
                },
                {
                    'name': 'Archaeplastida',
                    'description': 'Land plants, green algae, red algae, and glaucophytes'
                },
            ]
        }
    }
}


def raiseException(logger=None):
    """
    Used to test logger.exceptions.
    Use like:
    with self.assertRaises(ValueError):
        raiseException()
    """
    try:
        raise ValueError("Test Error")
    except ValueError:
        logger.exception(TEST_MSG)
        raise


class TestRemoveEntriesMixin(object):
    def remove_test_entries(self, test_key="msg.test"):
        """
        Remove all current test entries.
        Called in setUp and tearDown.
        TODO: Remove entries from timestamp collection
        """
        # Drop the timetamp collection completely
        self.handler.get_db().command("dropDatabase")

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({test_key: True}).count())


class TestBaseMongoLogHandler(TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        self.logger = logging.getLogger("test.base.reference")

        self.handler = get_mongolog_handler("test.base.reference", show_logger_names=True)
        console.error("self.handler(%s)" % self.handler)
        self.collection = self.handler.get_collection()

        self.remove_test_entries()

    def test_middleware(self):
        console.debug(self)
        c = Client()
        response = c.get(reverse("home"))
        self.assertContains(response, "HERE YOU ARE ON monglog/home.html")

    def test_dot_in_key(self):
        console.debug(self)
        self.logger.info({
            'META': {
                'user.name': 'jfurr',
                '$user$name': 'jfurr',
                'META2': {
                    'blah.blah': 'blah',
                    '$blah$blah': 'blah',
                    'META3': {
                        'meta3.meta3': 'meta3',
                        '$meta$meta': 'meta3',
                    }
                }
            },
            'user.name': 'janedoe',
            '$user$name': 'joeblow'
        })

    def test_write_concern(self):
        console.debug(self)
        self.logging = logging.getLogger("test.base.reference.w0")
        self.test_basehandler_exception()

    def test_valid_record_type(self):
        console.debug(self)
        record_type = LOGGING['handlers']['test_base_invalid']['record_type']
        LOGGING['handlers']['test_base_invalid']['record_type'] = 'invalid type'
        with self.assertRaises(ValueError):
            logging.config.dictConfig(LOGGING)

        # Reset the log handler
        LOGGING['handlers']['test_base_invalid']['record_type'] = record_type
        logging.config.dictConfig(LOGGING)

    def test_connection_error(self):
        console.debug(self)
        if pymongo_major_version >= 3:
            with self.assertRaises(pymongo.errors.ServerSelectionTimeoutError):
                self.handler.connect(test=True)

    def test_basehandler_exception(self):
        console.debug(self)
        with self.assertRaises(ValueError):
            raiseException(self.logger)

        records = self.collection.find({
            'msg.test': True,
            'msg.Life.Domain.Eukaryota.name': "Archaeplastida",
            'levelname': 'ERROR'
        })
        self.assertEqual(1, records.count())

        expected_keys = [
            u'threadName',
            u'name',
            u'thread',
            u'relativeCreated',
            u'process',
            u'args',
            u'filename',
            u'module',
            u'funcName',
            u'levelno',
            u'processName',
            u'created',
            u'msecs',
            u'msg',
            u'exc_info',
            u'exc_text',
            u'pathname',
            u'_id',
            u'levelname',
            u'lineno',
            u'time',
            u'uuid',
        ]
        # To make test pass on python 3 version
        if sys.version_info[0] >= 3:
            expected_keys.append(u'stack_info')

        record = records[0]
        self.assertEqual(
            set(record.keys()),
            set(expected_keys)
        )

        self.assertIn('tests.py', record['pathname'])

        # Now test that the nested ValueError was successfully converted to a unicode str.
        try:
            # unicode will throw a NameError in Python 3
            self.assertEqual(unicode, type(record['msg']['Life']['Domain']['Bacteria'][0]['name']))
        except NameError:
            self.assertEqual(str, type(record['msg']['Life']['Domain']['Bacteria'][0]['name']))

        self.logger.info("Just some friendly info")
        self.logger.error("Just some friendly info")
        self.logger.debug("Just some friendly info")

    def test_str_unicode_mongologhandler(self):
        console.debug(self)
        self.assertEqual(self.handler.connection, u"%s" % self.handler)
        self.assertEqual(self.handler.connection, "%s" % self.handler)


class TestSimpleMongoLogHandler_Embedded(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        console.debug(self)
        self.logger = logging.getLogger('test.embedded')
        self.handler = get_mongolog_handler('test.embedded')
        self.collection = self.handler.get_collection()

        self.remove_test_entries()

        self.expected_keys = set([
            'dates',
            'uuid',
            'thread',
            'level',
            'process',
            'exception',
            'module',
            'filename',
            'func',
            'created',
            'msg',
            'path',
            'line',
            '_id',
            'name',
            'counter',
        ])

    def test_missing_connection_key(self):
        LOGGING['handlers']['simple_no_connection'] = {
            'level': 'DEBUG',
            # Uncomment section to play with SimpleMongoLogHandler
            'class': 'mongolog.SimpleMongoLogHandler',
        }
        LOGGING['loggers']['simple.no.connection'] = {
            'level': 'DEBUG',
            'handlers': ['simple_no_connection'],
            'propagate': True
        }
        with self.assertRaises(ValueError):
            logging.config.dictConfig(LOGGING)

        del LOGGING['handlers']['simple_no_connection']
        del LOGGING['loggers']['simple.no.connection']

    def test_exception(self):
        console.debug(self)
        with self.assertRaises(ValueError):
            raiseException(self.logger)

        records = self.collection.find({
            'msg.test': True,
            'msg.Life.Domain.Eukaryota.name': "Archaeplastida",
            'level': 'ERROR'
        })
        self.assertEqual(1, records.count())

        record = records[0]
        self.assertEqual(
            set(record.keys()),
            self.expected_keys
        )

        # Verify that the dates field has 1 item
        self.assertEqual(1, len(record['dates']))

        # now create anthe rduplicate entry and show that only one record is still present
        # however now it should have 2 values in 'dates'
        with self.assertRaises(ValueError):
            raiseException(self.logger)

        records = self.collection.find({
            'msg.test': True,
            'msg.Life.Domain.Eukaryota.name': "Archaeplastida",
            'level': 'ERROR'
        })
        self.assertEqual(1, records.count())
        record = records[0]
        # should have two values in dates now
        self.assertEqual(2, len(record['dates']))

        # Now check the exceptoin keys
        self.assertEqual(
            set(record['exception'].keys()),
            set(['info', 'trace'])
        )


class TestSimpleMongoLogHandler_Reference(unittest.TestCase, TestRemoveEntriesMixin):
    """
    Test the mongolog reference storage capability.
    In 'reference' mode there are two collections created
    1) mongolog that holds that latest record and a single 'date'
    2) timestamp collection that holds that individual timestamps

    These two collections are related to each other via the uuid key.
    """
    def setUp(self):
        self.logger = logging.getLogger('test.reference')
        self.handler = get_mongolog_handler('test.reference')
        self.collection = self.handler.get_collection()
        self.remove_test_entries()

    def test_logstructure_simple_reference(self):
        """
        Test the simple log record structure
        """
        console.debug(self)

        # Used in test dictionaries to test mongo serialization
        SMH_Obj = SimpleMongoLogHandler(connection=LOGGING['handlers']['simple']['connection'])

        # now test a serializable dict with an exception call
        log_msg = {'test': True, 'fruits': ['apple', 'orange'], 'error': str(ValueError), 'handler': str(SMH_Obj)}
        expected_keys = set([
            '_id', 'exception', 'name', 'thread', 'time',
            'process', 'level', 'msg', 'path', 'module',
            'line', 'func', 'filename', 'uuid'
        ])

        try:
            raise ValueError
        except ValueError:
            self.logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': ['apple', 'orange']})
        self.assertEqual(set(rec.keys()), expected_keys)

        # Python 2 duplicate entry test
        log_msg = {'test': True, 'fruits': ['apple', 'orange'], 'error': str(ValueError), 'handler': str(SMH_Obj)}
        try:
            raise ValueError
        except ValueError:
            self.logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': ['apple', 'orange']})
        self.assertEqual(set(rec.keys()), expected_keys)

        # Now try an exception log with a complex log msg.
        try:
            raise ValueError
        except ValueError:
            log_msg = {
                'test': True,
                'fruits': [
                    'apple',
                    'orange',
                    {'tomatoes': ['roma', 'kmato', 'cherry', ValueError, 'plum']},
                    {},
                    {}
                ],
                'object': SimpleMongoLogHandler,
                'instance': SMH_Obj,
            }
            self.logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': {'$in': ['apple', 'orange']}})
        self.assertEqual(set(rec.keys()), expected_keys)


class TestVerboseMongoLogHandler(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        console.debug(self)
        self.logger = logging.getLogger("test.verbose")
        self.handler = get_mongolog_handler("test.verbose")
        self.collection = self.handler.get_collection()

        self.remove_test_entries(test_key="info.msg.test")

    def test_logstructure_verbose_exception(self):
        """
        Test the verbose log record strucute
        """
        console.debug(self)
        with self.assertRaises(ValueError):
            raiseException(self.logger)

        records = self.collection.find({
            'info.msg.test': True,
            'info.msg.Life.Domain.Eukaryota.name': "Archaeplastida",
            'level.name': 'ERROR'
        })
        self.assertEqual(1, records.count())

        record = records[0]
        self.assertEqual(
            set(record.keys()),
            set(['info', 'exception', 'time', 'level', 'name', 'thread', 'process', '_id', 'uuid'])
        )

        self.assertEqual(
            set(record['info'].keys()),
            set(["filename", "func", "line", "module", "msg", "path"])
        )

        for entry in ['thread', 'process', 'level']:
            self.assertEqual(
                set(record[entry].keys()),
                set(['name', 'num'])
            )

        self.assertIn('tests.py', record['info']['path'])

    def test_logstructure_verbose_debug_info_warn(self):
        """
        TODO:  Beef this test up a bit
        """
        console.debug(self)
        self.handler.setLevel("WARNING")
        log_msg = {'test': True, 'msg': 'WARNING', 'msg2': 'DANGER'}
        query = {
            'info.msg.test': log_msg['test'],
            'info.msg.msg': log_msg['msg'],
            'info.msg.msg2': log_msg['msg2'],
            'level.name': 'WARNING'
        }
        self.logger.warn(log_msg)
        self.assertEqual(1, self.collection.find(query).count())

        rec = self.collection.find_one(query)
        self.assertEqual(
            set(rec.keys()),
            set(['info', 'name', 'thread', 'level', 'process', 'time', '_id', 'uuid'])
        )

        for key in ['process', 'level', 'thread']:
            self.assertEqual(
                set(rec[key].keys()),
                set(['num', 'name'])
            )

        self.assertEqual(rec['thread']['name'], "MainThread")
        self.assertEqual(rec['info']['filename'], "tests.py")
        self.assertEqual(rec['process']['name'], "MainProcess")


class TestHttpLogHandler(unittest.TestCase):
    def setUp(self):
        console.debug(self)
        self.logger = logging.getLogger("test.http")
        self.handler = get_mongolog_handler("test.http")
        self.collection = self.handler.get_collection()
        console.error("self.collection(%s)" % self.collection)

    @skipIf(sys.version_info.major == 3, "SKipping TestHttpLogHandler.test_timeout because of python version")
    def test_timeout(self):
        console.debug(self)
        timeout = LOGGING['handlers']['test_http_invalid']['timeout']
        LOGGING['handlers']['test_http_invalid']['timeout'] = 1

        logging.config.dictConfig(LOGGING)

        self.logger = logging.getLogger("test.http")

        with self.assertRaises(ConnectionError):
            self.logger.warn("Danger Will Robinson!")

        LOGGING['handlers']['test_http_invalid']['timeout'] = timeout
        logging.config.dictConfig(LOGGING)

    @skipIf(sys.version_info.major == 3, "SKipping TestHttpLogHandler.test_invalid_connection because of python version")
    def test_invalid_connection(self):
        console.debug(self)
        with self.assertRaises(ConnectionError):
            self.logger.warn("Danger Will Robinson!")


class TestManagementCommands(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        console.debug(self)
        self.logger = logging.getLogger('test.reference')
        self.handler = get_mongolog_handler('test.reference')
        self.collection = self.handler.get_collection()

        self.remove_test_entries()
        self.remove_test_entries(test_key='info.msg.test')

    def test_analog(self):
        console.debug(self)
        self.logger.debug({'test': True, 'logger': 'Debug'})
        self.logger.info({'test': True, 'logger': 'Info'})
        self.logger.warn({'test': True, 'logger': 'Warn'})
        self.logger.error({'test': True, 'logger': 'Error'})
        self.logger.critical({'test': True, 'logger': 'Critical'})

        call_command('analog', limit=10, query='{"name": "root"}')

        with self.assertRaises(NotImplementedError):
            call_command('analog', limit=20, tail=True)


class TestPerformanceTests(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        self.handler = get_mongolog_handler('test.embedded')

        # Get some pointers to the collections for easy querying
        self.collection = self.handler.get_collection()
        self.timestamp = self.handler.get_timestamp_collection()

        self.remove_test_entries()

        # TODO Do you need this?
        self.remove_test_entries(test_key='msg.Test')
        self.iterations = 100

    def _check_embedded_results(self, results, iterations):
        self.assertEqual(1, results.count())
        rec = results[0]
        self.assertEqual(iterations, rec['counter'])

        expected_date_len = iterations
        if iterations > self.handler.max_keep:
            expected_date_len = self.handler.max_keep

        if len(rec['dates']) > expected_date_len:
            console.error("GREATER: date(%s)", rec['dates'])

        self.assertEqual(len(rec['dates']), expected_date_len)

    def test_embedded(self):
        console.debug(self)
        self.logger = logging.getLogger('test.embedded')
        console.info("Starting embedded test:  max_keep(%s) iteration(%s)", self.handler.max_keep, self.iterations)

        start = time.time()
        for i in range(self.iterations):
            self.logger.info({'Test': True, 'Test1': 1})
            results = self.collection.find({'msg.Test': True, 'msg.Test1': 1})
            self._check_embedded_results(results, i + 1)

        end = time.time()
        results = self.collection.find({'msg.Test': True})
        self._check_embedded_results(results, self.iterations)
        console.warn("Test time: %s", end - start)

        # rerun with larger max_keep
        max_keep = LOGGING['handlers']['test_embedded']['max_keep']
        LOGGING['handlers']['test_embedded']['max_keep'] = 50
        logging.config.dictConfig(LOGGING)
        self.setUp()
        self.logger = logging.getLogger('test.embedded')

        console.info("Starting embedded test:  max_keep(%s) iteration(%s)", self.handler.max_keep, self.iterations)

        start = time.time()
        for i in range(self.iterations):
            self.logger.info({'Test': True})
            results = self.collection.find({'msg.Test': True})
            self._check_embedded_results(results, i + 1)
        end = time.time()
        results = self.collection.find({'msg.Test': True})
        self._check_embedded_results(results, self.iterations)
        console.warn("Test time: %s", end - start)

        LOGGING['handlers']['test_embedded']['max_keep'] = max_keep
        logging.config.dictConfig(LOGGING)
        self.setUp()
        self.logger = logging.getLogger('test.embedded')

    def _check_reference_results(self, results, i):
        # confirm that only one document is ever created for the same message
        self.assertEqual(1, len(results))
        uuid = results[0]['uuid']
        ts_results = self.timestamp.find({'uuid': uuid})
        td_results = list(ts_results)
        self.assertEqual(i + 1, len(td_results))

    def test_reference(self):
        console.debug(self)
        self.logger = logging.getLogger('test.reference')
        console.info("Starting embedded test:  max_keep(%s) iteration(%s)", self.handler.max_keep, self.iterations)

        start = time.time()
        for i in range(self.iterations):
            self.logger.info({'Test': True, 'Test1': 1})
            results = list(self.collection.find({'msg.Test': True, 'msg.Test1': 1}))

            self._check_reference_results(results, i)

        end = time.time()
        self.logger.info("Total time %s" % (end - start))


class MongoLogUtilsTests(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        self.handler = get_mongolog_handler('test.embedded')

        # Get some pointers to the collections for easy querying
        self.collection = self.handler.get_collection()
        self.timestamp = self.handler.get_timestamp_collection()
        self.logger = logging.getLogger('test.embedded')

        self.remove_test_entries()

    def test_find_for_embedded(self):
        console.debug(self)
        Mongolog.LOGGER = 'test.embedded'
        info_items = [
            {'location': {'country': 'USA', 'state': 'WA', 'city': 'Puyallup'}},
            {'location': {'country': 'USA', 'state': 'WA', 'city': 'Seattle'}},
            {'location': {'country': 'USA', 'state': 'MA', 'city': 'Boston'}},
            {'location': {'country': 'USA', 'state': 'MS', 'city': 'Greenville'}},
            {'location': {'country': 'France', 'region': 'Normandy', 'city': 'Rouen'}},
            {'location': {'country': 'France', 'region': 'Île-de-France', 'city': 'Paris'}},
        ]
        for item in info_items:
            self.logger.info(item)

        warn_items = [
            {'location': {'country': 'France', 'region': 'Normandy', 'city': 'Caen'}},
            {'location': {'country': 'France', 'region': 'Normandy', 'city': 'Bayeux'}},
            {'location': {'country': 'USA', 'state': 'MA', 'city': 'Framingham'}},
        ]
        for item in warn_items:
            self.logger.warn(item)

        critical_items = [
            {'location': {'country': 'Canada', 'Province': 'Quebec Ontario', 'city': 'Quebec City'}},
            {'location': {'country': 'Canada', 'Province': 'Quebec Ontario', 'city': 'Toronto'}},
        ]

        for item in critical_items:
            self.logger.critical(item)

        results = Mongolog.find(query={'msg.location': {'$exists': True}})
        self.assertEqual(11, len(list(results)))

        results = Mongolog.find(level='INFO')
        self.assertEqual(6, len(list(results)))

        # Test limit
        results = Mongolog.find(level='INFO', limit=3)
        self.assertEqual(3, len(list(results)))

        # Test search by name
        results = Mongolog.find(logger="test.embedded")
        self.assertEqual(11, len(list(results)))

        results = Mongolog.find(query={'msg.location.region': {'$exists': True}})
        self.assertEqual(4, len(list(results)))

        results = Mongolog.find(query={'msg.location.region': {'$exists': True}}, level='ERROR')
        self.assertEqual(0, len(list(results)))

        results = Mongolog.find(query={'msg.location.region': {'$exists': True}}, level='WARNING')
        self.assertEqual(2, len(list(results)))

        results = Mongolog.find(level='CRITICAL')
        self.assertEqual(2, len(list(results)))

        results = Mongolog.find(level='CRITICAL', query={'msg.location.city': 'Quebec City'})
        self.assertEqual(1, len(list(results)))

        # Test uuid path.
        results = Mongolog.find(uuid='no-results')
        self.assertEqual(0, len(list(results)))

        # Now test projection
        query = {'msg.location.city': 'Quebec City'}
        level = 'CRITICAL'
        results = Mongolog.find(level=level, query=query, project={'msg': 1})
        results = list(results)
        self.assertEqual(set(['_id', 'msg']), set(results[0].keys()))

        results = Mongolog.find(level=level, query=query, project={'msg': 1, '_id': 0})
        results = list(results)
        self.assertEqual(set(['msg']), set(results[0].keys()))

        results = Mongolog.find(level=level, query=query, project={'msg': 1, '_id': 0, 'level': 1})
        results = list(results)
        self.assertEqual(set(['msg', 'level']), set(results[0].keys()))


class FlakeTests(unittest.TestCase):
    # flake8 --ignore=E402,F82
    def test_flak8(self):
        cmd = 'flake8 --ignore=E402,F82'
        logger = logging.getLogger("console")
        logger.debug(self)
        try:
            subprocess.check_output([cmd], shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            logger.critical("----------------- Please Fix flake8 errors -------------------")
            os.system(cmd)
            logger.critical("--------------------------------------------------------------")
            raise
