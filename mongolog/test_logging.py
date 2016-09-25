LOGGING = {
    'version': 1,
    'handlers': {
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
        'console': {
            'level': 'DEBUG',
            'class': 'settings.colorlog.ColorLogHandler',
            'info': 'white',
            'stream': 'ext://sys.stdout',
        },
        'http_invalid': {
            'level': 'DEBUG',
            # This section for HttpLogHandler
            'class': 'mongolog.HttpLogHandler',
            # Interesting Note:  requests 2.8.1 will turn this into a GET if it's missing a trailing slash
            # We automagically add the trailing slash
            'client_auth': 'http://192.168.33.51/4e487f07a84011e5a3403c15c2bcc424',
            'verbose': True,
            'timeout': 90,
            
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
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
        'test.http': {
            'level': 'DEBUG',
            'handlers': ['http_invalid'],
            'propagate': True,
        }
    },
}