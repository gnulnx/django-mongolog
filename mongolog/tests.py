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
from django.test import TestCase
import logging
import pymongo
pymongo_major_version = int(pymongo.version.split(".")[0])

from mongolog.handlers import MongoLogHandler

# Must instantiate root logger in order to access the correct 
# monglog collection from the MongoLogHandler
logger = logging.getLogger()


class TestLogLevels(TestCase):
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
        self.collection = self.get_monglog_collection()

        # Check for an preexsting mongolog test entries
        self.remove_test_entries()

    def tearDown(self):
        self.remove_test_entries()

    def get_monglog_collection(self):
        """
        Get the collection used by the first MongoLogHandler 
        found in the root loggers list of handlers. 
        """
        for handler in logger.handlers:
            if isinstance(handler, MongoLogHandler):
                self.handler = handler
                self.handler.setLevel("DEBUG")
                self.collection = self.handler.collection
                #self.handler.setLevel("ERROR")
                break

        if not hasattr(self, 'collection'):
            raise ValueError("Perhaps you didn't a monglog handler?", self.handler.__dict__)

        return self.collection

    def remove_test_entries(self):
        """
        Remove all current test entries
        Called in setUp and tearDown
        """
        if pymongo_major_version < 3:
            self.collection.remove({self.test_key: True})
        else:
            self.collection.delete_many({self.test_key: True})

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({self.test_key: True}).count())
    
    def test_info_verbose(self):
        # set level=DEBUG and log a message and retrieve it.
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
        Test the basic structure of a log record
        """
        self.handler.setLevel("WARNING")
        self.handler.set_record_type("verbose")
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

    def test_debug_verbose(self):
        self.handler.set_record_type("verbose")
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
        self.handler.set_record_type("verbose")
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

if __name__ == '__main__':
    unittest.main()
