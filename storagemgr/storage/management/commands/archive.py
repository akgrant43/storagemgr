from os.path import isdir

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from os.path import abspath

from storage.archiver import VideoArchiver, ImageArchiver, Archiver

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Archive the supplied directory tree'

    def add_arguments(self, parser):
        parser.add_argument('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        parser.add_argument('--break-on-add',
            action='store_true',
            dest='break_on_add',
            default=False,
            help='Load pdb and halt before adding files'),
        parser.add_argument('--images',
            action='store_true',
            dest='images',
            default=False,
            help="Archive images"),
        parser.add_argument('--videos',
            action='store_true',
            dest='videos',
            default=False,
            help="Archive videos"),
        parser.add_argument('--media',
            action='store_true',
            dest='media',
            default=False,
            help="Archive media (images & video)"),
        parser.add_argument('--files',
            action='store_true',
            dest='allfiles',
            default=False,
            help="Archive all files - being implemented"),
        parser.add_argument('srcdir',
            help="Archive source directory")
        parser.add_argument('dstdir', nargs='?',
            help="Archive source directory")

    def handle(self, *args, **options):

        logger.info("Archive starting")
        if options['debug']:
            import pdb
            pdb.set_trace()

        logger.info("Archiving: {0}".format(abspath(options['srcdir'])))

        if not isdir(options['srcdir']):
            msg = "Supplied path is not a directory: {0}".format(options['srcdir'])
            logger.fatal(msg)
            raise CommandError(msg)

        if options['images'] or options['media']:
            dest = settings.IMAGES_ARCHIVE
            archiver = ImageArchiver(options['srcdir'], dest, break_on_add=options['break_on_add'])
            archiver.archive()

        if options['videos'] or options['media']:
            dest = settings.IMAGES_ARCHIVE
            archiver = VideoArchiver(options['srcdir'], dest, break_on_add=options['break_on_add'])
            archiver.archive()

        if options['allfiles']:
            import pdb; pdb.set_trace()
            dest = options['dstdir']
            archiver = FileArchiver(args[0], dest, break_on_add=options['break_on_add'])
            archiver.archive()

        logger.info("Archive finished")

        return
