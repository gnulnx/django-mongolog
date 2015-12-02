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
                self.collection = handler.collection
                break

        if not hasattr(self, 'collection'):
            raise ValueError("Perhaps you didn't a monglog handler?", self.handler.__dict__)

        return self.collection

    def remove_test_entries(self):
        """
        Remove all current test entries
        Called in setUp and tearDown
        """
        self.collection.delete_many({self.test_key: True})

        # Ensure that we don't have any test entries
        self.assertEqual(0, self.collection.find({self.test_key: True}).count())

    
    def test_info(self):
        logger.info({'test': True, 'msg': 'INFO TEST'})
        self.assertEqual(
            1,
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'INFO TEST',
                'level.name': 'INFO'
            }).count()
        )

    def test_debug(self):
        logger.debug({'test': True, 'msg': 'DEBUG TEST'})
        self.assertEqual(
            1,
            self.collection.find({
                self.test_key: True, 
                'info.msg.msg': 'DEBUG TEST',
                'level.name': 'DEBUG'
            }).count()
        )

if __name__ == '__main__':
    unittest.main()

# Create your tests here.
