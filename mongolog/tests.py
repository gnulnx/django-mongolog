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
import json
from logging import config
import pymongo
pymongo_major_version = int(pymongo.version.split(".")[0])

from mongolog.handlers import (
    get_mongolog_handler, 
    MongoLogHandler, 
    SimpleMongoLogHandler,
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
            # record can be simple/verbose.  Default is verbose
            'record_type': 'simple',

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True
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

class TestBaseMongoLogHandler(unittest.TestCase):
    def setUp(self):
        LOGGING['handlers']['mongolog']['class'] = 'mongolog.BaseMongoLogHandler'
        logging.config.dictConfig(LOGGING)
        self.handler = get_mongolog_handler()
        self.collection = self.handler.get_collection()

        self.remove_test_entries()

    def remove_test_entries(self):
        """
        Remove all current test entries
        Called in setUp and tearDown
        """
        if pymongo_major_version < 3:
            self.collection.remove({'msg.test': True})
        else:
            self.collection.delete_many({'msg.test': True})

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({'msg.test': True}).count())

    def test_base_handler(self):
        test_msg = {
            'test':  True,  # String so we can remove test entries
            'test class': 'TestBaseMongoLogHandler',
            'Life': {
                'Domain': {
                    'Bacteria': [
                        {
                        'name':  ValueError,
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
                            'name':'Amoebozoa',
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
            try:
                raise ValueError("Test Error")
            except ValueError:
                logger.exception(test_msg)
                raise

        with self.assertRaises(ValueError):
            raiseException()

        query = {
            'msg.test': True, 
            'msg.Life.Domain.Eukaryota.name': "Archaeplastida",
            'levelname': 'ERROR'
        }
        records = self.collection.find(query)
        self.assertEqual(1, records.count())


        record = records[0]
        self.assertEqual(
            record.keys(),
            [
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
                u'lineno'
            ]
        )

        try:
            # unicode will throw a nameerror in Python 3
            self.assertEqual(unicode, type(record['msg']['Life']['Domain']['Bacteria'][0]['name'])) 
        except NameError:
            self.assertEqual(str, type(record['msg']['Life']['Domain']['Bacteria'][0]['name'])) 
        

class TestLogLevels(unittest.TestCase):
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

    # The basic key that should be part of every log messgage
    test_key = 'info.msg.test'

    def setUp(self):
        self.handler = get_mongolog_handler()
        #self.handler = MongoLogHandler.handler()
        self.collection = self.handler.get_collection()
        self.handler.setLevel("DEBUG")

        # Check for any preexsting mongolog test entries
        self.remove_test_entries()

    def tearDown(self):
        self.remove_test_entries()

    def test_str_unicode_mongologhandler(self):
        self.assertEqual(self.handler.connection, u"%s" % self.handler)
        self.assertEqual(self.handler.connection, "%s" % self.handler)

    def remove_test_entries(self):
        """
        Remove all current test entries
        Called in setUp and tearDown
        """
        if pymongo_major_version < 3:
            self.collection.remove({'info.msg.test': True})
            self.collection.remove({'msg.test': True})
        else:
            self.collection.delete_many({'info.msg.test': True})
            self.collection.delete_many({'msg.test': True})

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({self.test_key: True}).count())

    def test_set_record_type(self):
        with self.assertRaises(ValueError):
            self.handler.set_record_type("bad type")
    
    def test_info_verbose(self):
        # set level=DEBUG and log a message and retrieve it.
        self.handler.set_record_type(MongoLogHandler.VERBOSE)
        self.handler.setLevel("INFO")
        self.handler.set_record_type("verbose")
        logger.info({'test': True, 'msg': 'INFO TEST'})
        self.assertEqual(
            1,
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'INFO TEST',
                'level.name': 'INFO'
            }).count()
        )

        # Bump the log level up to INFO and show that
        # we do log another message because we are using the
        # logger.info(...) method
        self.handler.setLevel("INFO")
        logger.info({'test': True, 'msg': 'INFO TEST'})
        self.assertEqual(
            2,
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'INFO TEST',
                'level.name': 'INFO'
            }).count()
        )

        # Show that at level=ERROR no new message is logged
        self.handler.setLevel("ERROR")
        logger.info({'test': True, 'msg': 'INFO TEST'})
        self.assertEqual(
            2,  # count same as previous count
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'INFO TEST',
                'level.name': 'INFO'
            }).count()
        )

    def test_logstructure_verbose(self):
        """
        Test the verbose log record strucute
        """
        self.handler.set_record_type(MongoLogHandler.VERBOSE)
        self.handler.setLevel("WARNING")
        log_msg = {'test': True, 'msg': 'WARNING', 'msg2': 'DANGER'}
        query = {
            self.test_key: log_msg['test'], 
            'info.msg.msg': log_msg['msg'],
            'info.msg.msg2': log_msg['msg2'],
            'level.name': 'WARNING'
        }
        logger.warn(log_msg)
        self.assertEqual(1, self.collection.find(query).count())

        rec = self.collection.find_one(query)
        self.assertEqual(
            set(rec.keys()), 
            set(['info', 'name', 'thread', 'level', 'process', 'time', '_id'])
        )

        self.assertEqual(
            set(rec['time'].keys()),
            set(['utc', 'loc'])
        )

        for key in ['process', 'level', 'thread']:
          self.assertEqual(
                set(rec[key].keys()),
                set(['num', 'name'])
            )

        self.assertEqual(rec['thread']['name'], "MainThread")
        self.assertEqual(rec['info']['filename'], "tests.py")
        self.assertEqual(rec['process']['name'], "MainProcess")

    def test_logstructure_simple(self):
        """
        Test the simple log record structure
        """
        self.handler.set_record_type(MongoLogHandler.SIMPLE)
        self.handler.setLevel("DEBUG")
      
        
        # now test a serielazable dict with an exception call
        log_msg = {'test': True, 'fruits': ['apple', 'orange'], 'error': str(ValueError), 'handler': str(MongoLogHandler())}
        try:
            raise ValueError
        except ValueError as e:
            logger.exception(log_msg)

        rec = self.collection.find_one({'msg.fruits': ['apple', 'orange']})
        self.assertEqual(
            set(rec.keys()),
            set(['_id', 'exception', 'name', 'thread', 'time', 'process', 'level', 'msg', 'path', 'module', 'line', 'func', 'filename'])
        )

        # Now try an exception log with a complex log msg.
        try:
            raise ValueError
        except ValueError as e:
            logger.exception({
                'test': True,
                'fruits': [
                    'apple',
                    'orange',
                    {'tomatoes': ['roma', 'kmato', 'cherry', ValueError, 'plum']},
                    {},
                    {}
                ],
                'object': MongoLogHandler,
                'instance': MongoLogHandler(),
            })

        rec = self.collection.find_one({'msg.fruits': {'$in': ['apple', 'orange']}})
        self.assertEqual(
            set(rec.keys()),
            set(['_id', 'exception', 'name', 'thread', 'time', 'process', 'level', 'msg', 'path', 'module', 'line', 'func', 'filename'])
        )

        print "LEAVING"
        

    def test_debug_verbose(self):
        self.handler.set_record_type(MongoLogHandler.VERBOSE)
        logger.debug({'test': True, 'msg': 'DEBUG TEST'})
        self.assertEqual(
            1,
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'DEBUG TEST',
                'level.name': 'DEBUG'
            }).count()
        )

    def test_exception_verbose(self):
        self.handler.set_record_type(MongoLogHandler.VERBOSE)
        try:
            raise ValueError()
        except ValueError:
            logger.exception({'test': True, 'msg': 'EXCEPTION TEST'})

        query = {
            self.test_key: True, 
            'info.msg.msg': 'EXCEPTION TEST',
            'level.name': 'ERROR'
        }
        self.assertEqual(1,self.collection.find(query).count())

        rec = self.collection.find_one(query)

        self.assertEqual(
            set(rec.keys()), 
            set(['info', 'name', 'thread', 'level', 'process', 'time', '_id', 'exception'])
        )

        self.assertEqual(
            set(rec['exception'].keys()),
            set(['info', 'trace'])  
        )
