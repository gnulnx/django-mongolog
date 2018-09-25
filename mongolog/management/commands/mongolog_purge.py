# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import logging
import logging.config
from datetime import timedelta

import pymongo
from pymongo import MongoClient

from mongolog.handlers import get_mongolog_handler

from django.utils import timezone
from django.core.management.base import BaseCommand

pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument  # noqa: F40

console = logging.getLogger('mongolog-int')

handler = get_mongolog_handler()
client = MongoClient(handler.connection)
db = client.mongolog


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

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.prev_object_id = None

    def purge(self):
        print("Purging all mongolog documents")

    def delete(self, **options):
        days = options['delete']
        console.warn("Looking for documents older than %s day's", days)

        query = {
            'created': {
                '$lte': timezone.now() - timedelta(days=days)
            }
        }

        total = db.mongolog.find(query).count()
        console.warn("Total docs to remove: %s", total)

        if not options['force']:
            ans = 'n'
            while 1:
                console.warn("Would you like to proceed?  Y/N")
                ans = input().strip()
                if ans.lower() not in ['y', 'yes', 'n', 'no']:
                    continue
                elif ans[0] == 'n':
                    console.info("You chose not to continue.  Bye!")
                    sys.exit(1)
                elif ans[1] == 'y':
                    break

        db.mongolog.delete_many(query)
        console.info("Total docs removed: %s", total)

    def handle(self, *args, **options):
        if options['purge']:
            self.purge()
        elif isinstance(options['delete'], int):
            self.delete(**options)
