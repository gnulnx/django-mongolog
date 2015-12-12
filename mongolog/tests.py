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
import sys
import pymongo
pymongo_major_version = int(pymongo.version.split(".")[0])

from mongolog.handlers import (
    get_mongolog_handler, SimpleMongoLogHandler
)

# Use plain python logging instead of django to decouple project
# from django versions
LOGGING = {
    'version': 1,
    'handlers': {
        'mongolog': {
            'level': 'DEBUG',
            'class': 'mongolog.SimpleMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 1,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': False
        },
    },
    'loggers': {
        '': {
            'handlers': ['mongolog'],
            'level': 'DEBUG',
            'propagate': True
        },
    },
}
# Must instantiate root logger in order to access the correct 
# monglog collection from the MongoLogHandler
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('')

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
                    'description': 'Just a bad description'
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


def raiseException():
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
        Remove all current test entries
        Called in setUp and tearDown
        """
        if pymongo_major_version < 3:
            self.collection.remove({test_key: True})
        else:
            self.collection.delete_many({test_key: True})

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({test_key: True}).count())


class TestBaseMongoLogHandler(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        
        LOGGING['handlers']['mongolog']['class'] = 'mongolog.BaseMongoLogHandler'
        logging.config.dictConfig(LOGGING)

        self.handler = get_mongolog_handler()
        self.collection = self.handler.get_collection()

        self.remove_test_entries()

    def test_connection_error(self):
        if pymongo_major_version >= 3:
            with self.assertRaises(pymongo.errors.ServerSelectionTimeoutError):
                self.handler.connect(test=True)

    def test_basehandler_exception(self):
        
        with self.assertRaises(ValueError):
            raiseException()

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
        
        logger.info("Just some friendly info")
        logger.error("Just some friendly info")
        logger.debug("Just some friendly info")
        
    def test_str_unicode_mongologhandler(self):
        self.assertEqual(self.handler.connection, u"%s" % self.handler)
        self.assertEqual(self.handler.connection, "%s" % self.handler)


class TestSimpleMongoLogHandler(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        LOGGING['handlers']['mongolog']['class'] = 'mongolog.SimpleMongoLogHandler'
        logging.config.dictConfig(LOGGING)
        self.handler = get_mongolog_handler()
        self.collection = self.handler.get_collection()

        self.remove_test_entries()

    def test_logstructure_simple(self):
        """
        Test the simple log record structure
        """

        self.handler.setLevel("DEBUG")

        # now test a serielazable dict with an exception call
        log_msg = {'test': True, 'fruits': ['apple', 'orange'], 'error': str(ValueError), 'handler': str(SimpleMongoLogHandler())}
        expected_keys = set([
            '_id', 'exception', 'name', 'thread', 'time', 
            'process', 'level', 'msg', 'path', 'module', 
            'line', 'func', 'filename', 'uuid'
        ])

        try:
            raise ValueError
        except ValueError:
            logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': ['apple', 'orange']})
        self.assertEqual(set(rec.keys()), expected_keys)

        # Python 2 duplicate entry test
        log_msg = {'test': True, 'fruits': ['apple', 'orange'], 'error': str(ValueError), 'handler': str(SimpleMongoLogHandler())}
        try:
            raise ValueError
        except ValueError:
            logger.exception(log_msg)

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
                'instance': SimpleMongoLogHandler(),
            }
            logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': {'$in': ['apple', 'orange']}})
        self.assertEqual(set(rec.keys()), expected_keys)
        
        
class TestVerboseMongoLogHandler(unittest.TestCase, TestRemoveEntriesMixin):
    def setUp(self):
        LOGGING['handlers']['mongolog']['class'] = 'mongolog.VerboseMongoLogHandler'
        logging.config.dictConfig(LOGGING)
        self.handler = get_mongolog_handler()
        self.collection = self.handler.get_collection()

        self.remove_test_entries(test_key="info.msg.test")

    def test_logstructure_verbose_exception(self):
        """
        Test the verbose log record strucute
        """
        with self.assertRaises(ValueError):
            raiseException()

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
        self.handler.setLevel("WARNING")
        log_msg = {'test': True, 'msg': 'WARNING', 'msg2': 'DANGER'}
        query = {
            'info.msg.test': log_msg['test'], 
            'info.msg.msg': log_msg['msg'],
            'info.msg.msg2': log_msg['msg2'],
            'level.name': 'WARNING'
        }
        logger.warn(log_msg)
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
