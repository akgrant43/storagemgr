#!/usr/bin/env python
"""Show slideshow for images in a given directory (recursively) in cycle.

If no directory is specified, it uses the current directory.
"""
import logging
import os
import platform
import sys
from collections import deque
from itertools import cycle

import Tkinter as tk

import Image
import ImageTk

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from storage.models import File
from slides.slideshow import Slideshow

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Run a slideshow with the supplied keywords'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        make_option('--nosort',
            action='store_true',
            dest='nosort',
            default=False,
            help="Don't sort the slides by date"),
        )

    def handle(self, *args, **options):

        if options['debug']:
            import pdb
            pdb.set_trace()

        logger.info("Slideshow starting")
        # Get the list of files
        files = File.objects
        for kw in args:
            files = files.filter(keyword__name__exact=kw)
        if not options['nosort']:
            files = files.order_by('date')
        image_filenames = [f.abspath for f in files.all()]
        Slideshow.fullscreen(image_filenames)
        logger.info("Slideshow finished")

        return

