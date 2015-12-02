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

class TestLogLevels(TestCase):

    def setUp(self):
        self.get_mongo_db()

    def tearDown(self):
        self.client.drop_database(self.db)

    def get_mongo_db(self):
        """
        First try to get the MongoClient from the settings configuration.
        If that fails then try a default connect.

        Once we have a client we create a test database:  mongolog__test
        """
        # Get the RootLogger so we can get access to the current mongo connect
        
        self.logger = logging.getLogger()
        for handler in self.logger.handlers:
            if isinstance(handler, MongoLogHandler):
                self.handler = handler
                self.logger.debug("Using MongoLogHandler from settings")
                self.client = handler.client
                break

        if not hasattr(self, 'client'):
            self.client = pymongo.MongoClient('mongodb://localhost:27017')

        self.db = self.client.mongolog__test
        return self.db
        
    def test_info(self):
        self.assertEqual('INFO', self.logger.info("INFO"))

if __name__ == '__main__':
    unittest.main()

# Create your tests here.
