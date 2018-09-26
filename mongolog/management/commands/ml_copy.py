# -*- coding: utf-8 -*-
"""
Management command to handle deletion of previous mongolog records.

Usage Examples:

# Used to migrate monoglog data from one collection to another
 ./manage.py ml_migrate {from_collection} {to_collectioj}
"""
from __future__ import print_function
import sys
import logging
import subprocess
from pymongo import MongoClient

from mongolog.handlers import get_mongolog_handler

from django.core.management.base import BaseCommand

console = logging.getLogger('mongolog-int')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--from', default='', type=str, action='store', dest='from',
            help='From Collection',
        )
        parser.add_argument(
            '-t', '--to', default='', type=str, action='store', dest='to',
            help='To Collection',
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

    def backup(self):
        """ Backup the collection before deleting """
        console.info("Backing up your documents...")
        cmd = 'mongodump --db mongolog'
        subprocess.check_call([cmd], shell=True)

    def handle(self, *args, **options):
        """ Main processing handle """
        handler = get_mongolog_handler()
        client = MongoClient(handler.connection)
        db = client.mongolog

        from_collection = getattr(db, options['from_collection'])
        from_collection.copyTo(options['to_collection'])
