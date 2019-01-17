#!/usr/bin/env python


class MissingConnectionError(ValueError):
    def __init__(self, *args, **kwargs):
        ValueError.__init__(self, *args, **kwargs)


class LogConfigError(ValueError):
    pass


class UnsupportedVersionError(ValueError):
    pass
