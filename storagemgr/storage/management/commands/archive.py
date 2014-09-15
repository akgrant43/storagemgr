from os.path import isdir

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from storage.archiver import VideoArchiver, ImageArchiver, Archiver

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Archive the supplied directory tree'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        make_option('--images',
            action='store_true',
            dest='images',
            default=False,
            help="Archive images"),
        make_option('--videos',
            action='store_true',
            dest='videos',
            default=False,
            help="Archive videos"),
        make_option('--media',
            action='store_true',
            dest='media',
            default=False,
            help="Archive media (images & video)"),
        make_option('--files',
            action='store_true',
            dest='allfiles',
            default=False,
            help="Archive all files - being implemented"),
        )

    def handle(self, *args, **options):

        logger.info("Archive starting")
        if options['debug']:
            import pdb
            pdb.set_trace()

        if not isdir(args[0]):
            msg = "Supplied path is not a directory: {0}".format(args[0])
            logger.fatal(msg)
            raise CommandError(msg)

        if options['images'] or options['media']:
            dest = settings.IMAGES_ARCHIVE
            archiver = ImageArchiver(args[0], dest)
            archiver.archive()

        if options['videos'] or options['media']:
            dest = settings.IMAGES_ARCHIVE
            archiver = VideoArchiver(args[0], dest)
            archiver.archive()

        if options['allfiles']:
            import pdb; pdb.set_trace()
            dest = args[1]
            archiver = FileArchiver(args[0], dest)
            archiver.archive()

        logger.info("Archive finished")

        return
