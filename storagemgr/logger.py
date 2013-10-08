#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


def init_logging(log_name=__name__):

    logger = logging.getLogger(log_name)
    logger.debug('Initialised logging for {0}'.format(log_name))
    return logger
