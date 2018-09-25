# -*- coding: utf-8 -*-
# !/usr/bin/env python
from __future__ import print_function
import logging
import logging.config
import django
import json
from datetime import datetime, timedelta

import pymongo
pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument  # noqa: F40
from pymongo import MongoClient

from mongolog.handlers import get_mongolog_handler
from mongolog.models import Mongolog

from django.utils import timezone
from django.core.management.base import BaseCommand

# Is this actually used?
logger = logging.getLogger('console')

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
            '-d', '--d', default=14, type=int, action='store', dest='delete',
            help='Remove documents more than -d={n} days old',
        )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.prev_object_id = None

    def purge(self):
        print("Purging all mongolog documents")

    def delete(self, **options):
        days = options['delete']
        query={
            'created': {
                '$lte': timezone.now() - timedelta(days=days)
            }
        }

        console.warn("Removing documents older than %s day's", days)
        #print("Removing documents older than %s day's" % days)
        total = db.mongolog.find(query).count()
        console.info("Total docs to remove: %s", total)
        #print("Total docs to remove: %s" % total)
        db.mongolog.delete_many(query)

    def handle(self, *args, **options):
        if options['purge']:
            self.purge()
        elif isinstance(options['delete'], int):
            self.delete(**options)
