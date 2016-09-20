# -*- coding: utf-8 -*-
#!/usr/bin/env python
from __future__ import print_function
import logging

import pymongo
pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument


from mongolog.handlers import get_mongolog_handler

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--limit', default=10, type=int, action='store', dest='limit',
            help='Limit Results',
        )

    def handle(self, *args, **options):
        handler = get_mongolog_handler()
        self.collection = handler.get_collection()
        print("Hello from AnaLog", options)
        print("Collection: ", self.collection)

        results = self.collection.find({}).limit(options['limit'])
        for r in results:
            print(r)
