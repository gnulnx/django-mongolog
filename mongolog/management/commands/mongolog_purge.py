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

logger = logging.getLogger('console')
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
        now = timezone.now()
        query_date = now - timedelta(days=days)
        print("now(%s) - query_date(%s)" % (now, query_date))
        print(db.mongolog)
        docs = list(Mongolog.find(query={'created': {'$lte': query_date}}))
        for i in Mongolog.find(query={'created': {'$lte': query_date}}):
            print(json.dumps(i, indent=4, sort_keys=True, default=str))
            db.mongolog
            #self.db..delete()
            #print("Delete called")

        print(Mongolog.find() )
        print("Total docs to remove: %s" % len(docs))
        print("Removing documents older than %s day's" % days)
        db.mongolog.delete_one(query_date)        

    def handle(self, *args, **options):
        if options['purge']:
            self.purge()
        elif isinstance(options['delete'], int):
            self.delete(**options)
