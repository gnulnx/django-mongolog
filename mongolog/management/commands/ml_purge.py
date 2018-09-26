# -*- coding: utf-8 -*-
"""
Management command to handle deletion of previous mongolog records.

Usage Examples:

# Delete all records alder than 54 day's AFTER backing up the current collection 'bulkupload'
 ./manage.py mongolog_purge -d 54 -b -c bulkupload

 # Delete all entries
./manage.py mongolog_purge -p -c bulkupload
"""
from __future__ import print_function
import sys
import logging
from datetime import timedelta
import subprocess
from pymongo import MongoClient

from mongolog.handlers import get_mongolog_handler

from django.utils import timezone
from django.core.management.base import BaseCommand

console = logging.getLogger('mongolog-int')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-p', '--purge', default=False, action='store_true', dest='purge',
            help='Remove all old results',
        )
        parser.add_argument(
            '-d', '--delete', default=14, type=int, action='store', dest='delete',
            help='Delete documents more than -d={n} days old',
        )
        parser.add_argument(
            '-f', '--force', default=False, action='store_true', dest='force',
            help='Do not prompt before removing documents',
        )
        parser.add_argument(
            '-b', '--backup', default=False, action='store_true', dest='backup',
            help='Backup collection before deleting',
        )
        parser.add_argument(
            '-l', '--logger', default='mongolog', type=str, action='store', dest='logger',
            help='Which mongolog logger to use.  The collection defined in the log handler will be used.',
        )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def confirm(self, **options):
        if not options['force']:
            while 1:
                console.warn("Would you like to proceed?  Y/N")
                ans = input().strip().lower()

                if ans not in ['y', 'yes', 'n', 'no']:
                    continue
                elif ans[0] == 'n':
                    console.info("You chose not to continue.  Bye!")
                    sys.exit(1)
                elif ans[0] == 'y':
                    break

        return True

    def purge(self, **options):
        """ Purge all records from the collection """
        console.warn("You are about to delete all mongolog documents!!!")

        if self.confirm(**options):
            total = self.collection.find({}).count()
            self.collection.delete_many({})
            console.warn("Total docs to remove: %s", total)

    def delete(self, **options):
        """ Delete all records older than --delete={n} """
        days = options['delete']
        console.warn("Looking for documents older than %s day's", days)

        query = {
            'created': {
                '$lte': timezone.now() - timedelta(days=days)
            }
        }

        total = self.collection.find(query).count()
        console.warn("Total docs to remove: %s", total)

        if self.confirm(**options):
            self.collection.delete_many(query)
            console.info("Total docs removed: %s", total)

    def backup(self):
        """ Backup the collection before deleting """
        console.info("Backing up your documents...")
        cmd = 'mongodump --db mongolog'
        subprocess.check_call([cmd], shell=True)

    def handle(self, *args, **options):
        """ Main processing handle """
        handler = get_mongolog_handler(logger_name=options['logger'])
        client = MongoClient(handler.connection)
        db = client.mongolog
        self.collection = getattr(db, handler.collection)

        if options['backup']:
            self.backup()

        if options['purge']:
            self.purge(**options)
        elif isinstance(options['delete'], int):
            self.delete(**options)
