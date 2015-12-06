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
    #def __str__(self):
    #    return json.dumps(self, sort_keys=True, indent=4, default=str)

    #def __repr__(self):
    #    return json.dumps(self, sort_keys=True, indent=4, default=str)
    #    return json.loads(json.dumps(self, default=str))
    pass
    

