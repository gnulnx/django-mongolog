# -*- coding: utf-8 -*-
# !/usr/bin/env python
from __future__ import print_function
import logging
import logging.config
import django
import json

import pymongo
pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument  # noqa: F40

from mongolog.handlers import get_mongolog_handler
from mongolog.models import Mongolog

from django.utils import timezone
from django.core.management.base import BaseCommand

logger = logging.getLogger('console')


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
        for i in list(Mongolog.find(query={'created': {'$lte': timezone.now()}})):
            print(i)

        print(Mongolog.find() )
        print("Removing documents older than %s day's" % days)

    def handle(self, *args, **options):
        if options['purge']:
            self.purge()
        elif options['delete']:
            self.delete(**options)
