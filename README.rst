MongoLog 
========

MongoLog is a simple Mongo based log handler that can be easly used
with standard python/django logging.

 .. image:: https://coveralls.io/repos/gnulnx/django-mongolog/badge.svg?branch=master&service=github :target: https://coveralls.io/github/gnulnx/django-mongolog?branch=master


 Please visit the `MongoLog Users Group<https://groups.google.com/forum/#!forum/mongolog-users>`_ with any questions/suggestions.   Thanks.

Quick start
----------- 

1. Add "mongolog" to your INSTALLED_APPS like this
    .. code:: python

        INSTALLED_APPS = (
            ...
            'mongolog',
        )

2. Add the SimpleMongoLoggerHandler to your LOGGING config.  
    .. code:: python

        LOGGING = {
            'version': 1,
            'handlers': {
                'mongolog': {
                    'level': 'DEBUG',
                    'class': 'mongolog.SimpleMongoLogHandler',
                    'connection': 'mongodb://localhost:27017'
                },
            },
            'loggers': {
                '': {
                    'handlers': ['mongolog'],
                    'level': 'DEBUG',
                    'propagate': True
                },
            },
        }

3) Start your management shell::

    ./manage.py shell

4) Create a couple of log entries
    .. code:: python
    
        import logging
        import pymongo
        logger = logging.getLogger(__name__)

    One of the cool things about mongolog is that it can log complex data structures
    in a way that makes them both human parsable and queryable.  So for instance if 
    we create a the following log message:

    .. code:: python

        
        # Pro Tip: You can copy and paste all of this
        
        LOG_MSG = {
            'test': True,  
            'test class': 'TestBaseMongoLogHandler',
            'Life': {
                'Domain': {
                    'Bacteria': [
                        {
                            'name': ValueError,  # intentional bad value
                            'description': 'Just a bad description'
                        }
                    ],
                    'Archaea': [],
                    'Eukaryota': [
                        {
                            'name': 'Excavata', 
                            'description': 'Various flagellate protozoa',
                        },
                        {   
                            'name': 'Amoebozoa',
                            'descritpion': 'most lobose amoeboids and slime moulds',
                        },
                        {
                            'name': 'Opisthokonta',
                            'description': 'animals, fungi, choanoflagellates, etc.',
                        },
                    ]
                } 
            }
        }

    Now let's log our message at each of the defined log levels...

    .. code:: python

        logger.debug(LOG_MSG)
        logger.info(LOG_MSG)
        logger.warn(LOG_MSG)
        logger.error(LOG_MSG)
        try:
            raise ValueError("Bad Value")
        except ValueError as e:
            logger.exception(LOG_MSG)

5) Now log into your mongo shell and look at some results
    .. code:: python

        ./mongo

        use mongolog
        db.mongolog.findOne({'level': "INFO"})

    Will produde a mongo document like:

    .. code:: python

        {
            "_id" : ObjectId("5664a22bdd162ca58f0693d2"),
            "name" : "__builtin__",
            "thread" : NumberLong("140735229362944"),
            "level" : "INFO",
            "process" : 42383,
            "module" : "<console>",
            "filename" : "<console>",
            "func" : "<module>",
            "time" : ISODate("2015-12-06T21:01:31.258Z"),
            "msg" : {
                "test" : true,
                "Life" : {
                    "Domain" : {
                        "Eukaryota" : [
                            {
                                "name" : "Excavata",
                                "description" : "Various flagellate protozoa"
                            },
                            {
                                "name" : "Amoebozoa",
                                "descritpion" : "most lobose amoeboids and slime moulds"
                            },
                            {
                                "name" : "Opisthokonta",
                                "description" : "animals, fungi, choanoflagellates, etc."
                            }
                        ],
                        "Archaea" : [ ],
                        "Bacteria" : [
                            {
                                "name" : "<type 'exceptions.ValueError'>",
                                "description" : "Just a bad description"
                            }
                        ]
                    }
                },
                "test class" : "TestBaseMongoLogHandler"
            },
            "path" : "<console>",
            "line" : 1
        }

    Take a look at the "msg" section and you will notice that all of the information from our LOG_MSG
    is contained under that key in standard mongo data structures.  This means that we can query 
    based on our log message.  For example in your mongo shell try the following queries:

    .. code:: python

        # Find all documents loggd with a 'test' key
        > db.mongolog.find({'msg.test': {$exists: true}}).count()
        5

        # Find all documents that have a  Eukaryota name in the list of  ["Amoebozoa", "Opisthokonta"]
        > db.mongolog.find({'msg.Life.Domain.Eukaryota.name': {$in: ["Amoebozoa", "Opisthokonta"]}}).count()
        1

        # Same as above but only those documents logged at level INFO
        >db.mongolog.find({
            'level': 'INFO',
            'msg.Life.Domain.Eukaryota.name': {$in: ["Amoebozoa", "Opisthokonta"]}, 
        }).count()
        1

        # And again at level ERROR.  
        >db.mongolog.find({
            'level': 'INFO',
            'msg.Life.Domain.Eukaryota.name': {$in: ["Amoebozoa", "Opisthokonta"]}, 
        }).count()
        2
        
        #Notice that now two records are returned.  This is because
        # logger.exception(...) also logs at level ERROR, but also notice that if when we
        # pretty print the records...
        >db.mongolog.find({
            'level': 'ERROR',
            'msg.Life.Domain.Eukaryota.name': {$in: ["Amoebozoa", "Opisthokonta"]}, 
        }).pretty()

        # one of the entries has exception info.  When running in a real environment
        # and not the console the 'trace' section will be populated with the full stack trace.
        "exception" : {
            "info" : [
                "<type 'exceptions.ValueError'>",
                "Bad Value",
                "<traceback object at 0x106853b90>"
            ],
            "trace" :
             null
        }

6) Future  Roadmap
    .. code:: python

    Currently mongolog has pretty solid support for logging aribtraty datastructures.  If it finds
    an object it doesn't know how to natively serialize it will try to convert it to str().  

    The next steps are to create a set of most used query operations for probing the log.

    I am very interested in feedback and feature requests from anyone using mongolog.
    If you are interested in contributing please fork the repo and start coding.  
    You can reach me through my account at github with any questions.
