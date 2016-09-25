LOGGING = {
    'version': 1,
    'handlers': {
        'mongolog': {
            'level': 'DEBUG',
            'class': 'mongolog.SimpleMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            # 'connection': 'mongodb://192.168.33.31:27017',
            'w': 1,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
        'test_reference': {
            'level': 'DEBUG',
            'class': 'mongolog.SimpleMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 1,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
        'test_embedded': {
            'level': 'DEBUG',
            'class': 'mongolog.SimpleMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 1,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'embedded',
        },
        'base_reference': {
            'level': 'DEBUG',
            'class': 'mongolog.BaseMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 1,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
        'base_reference_w0': {
            'level': 'DEBUG',
            'class': 'mongolog.BaseMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 0,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
        'base_invalid': {
            'level': 'DEBUG',
            'class': 'mongolog.BaseMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 0,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
        'verbose': {
            'level': 'DEBUG',
            'class': 'mongolog.VerboseMongoLogHandler',
            'connection': 'mongodb://localhost:27017',
            'w': 0,
            'j': False,

            # utc/local.  Only used with record_type=simple
            'time_zone': 'local',
            'verbose': True,
            'record_type': 'reference',
        },
    },
    'loggers': {
        '': {
            'handlers': ['mongolog'],
            'level': 'DEBUG',
            'propagate': True
        },
        #'mongolog': {
        #    'handlers': ['mongolog'],
        #    'level': 'DEBUG',
        #    'propagate': False
        #},
        'test': {
            'level': 'DEBUG',
            'propagate': False,
        },
        'test.reference': {
            'handlers': ['test_reference'],
        },
        'test.embedded': {
            'handlers': ['test_embedded'],
        },
        'test.base.reference': {
            'handlers': ['base_reference'],  
        },
        'test.base.reference.w0': {
            'handlers': ['base_reference_w0'],  
        },
        'test.base.invalid': {
            'handlers': ['base_invalid'],  
        },
        'test.verbose': {
            'handlers': ['verbose'],  
        },
    },
}