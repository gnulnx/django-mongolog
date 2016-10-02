#!/usr/bin/env python
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
import pymongo
from pymongo import MongoClient
pymongo_version = int(pymongo.version.split(".")[0])
if pymongo_version >= 3:
    from pymongo.collection import ReturnDocument  # noqa: F401


class Mongolog(object):
    """
    This class provides a set of queriable functions.
    """
    # If LOGGER is None we wil try and find the first available logger
    LOGGER = None

    @classmethod
    def find(cls, logger=None, query=None, project=None, uuid=None, level=None, limit=None, **kwargs):
        """
         return self.collection.aggregate([
            {"$match": query},
            {"$project": proj},
            {"$sort": {'created': pymongo.DESCENDING}},
            {"$limit": limit},
        ])
        """
        from mongolog.handlers import get_mongolog_handler

        logger = cls.LOGGER if cls.LOGGER else logger

        handler = get_mongolog_handler(logger_name=logger)
        client = MongoClient(handler.connection)
        db = client.mongolog

        aggregate_commands = []

        if not query:
            query = {}

        if uuid:
            query.update({'uuid': uuid})

        if level:
            query.update({'level': level})

        if logger:
            query.update({'name': logger})

        aggregate_commands.append({"$match": query})

        if project:
            aggregate_commands.append({"$project": project})

        aggregate_commands.append({"$sort": {'created': pymongo.DESCENDING}})

        if limit:
            aggregate_commands.append({"$limit": limit})

        results = db.mongolog.aggregate(aggregate_commands)
        return results['result'] if isinstance(results, dict) else results


class LogRecord(dict):
    """
    {
        "_id" : ObjectId("565cc24656c02c294614f740"),
        "info" : {
            "module" : "<console>",
            "filename" : "<console>",
            "func" : "<module>",
            "msg" : "DEBUG message",
            "path" : "<console>",
            "line" : 1
        },
        "name" : "mongo",
        "thread" : {
            "num" : NumberLong(140061052233472),
            "name" : "MainThread"
        },
        "level" : {
            "num" : 10,
            "name" : "DEBUG"
        },
        "process" : {
            "num" : 10566,
            "name" : "MainProcess"
        },
        "time" : {
        "utc" : ISODate("2015-11-30T21:40:22.494Z"),
            "loc" : ISODate("2015-11-30T21:40:22.494Z")
        }
    }
    """
    pass
