from os.path import isfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from storage.archiver import VideoArchiver, ImageArchiver, Archiver
from storage.smhash import smhash

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Hash the specified file'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        )

    def handle(self, *args, **options):

        logger.info("smhash starting")
        if options['debug']:
            import pdb
            pdb.set_trace()

        if not isfile(args[0]):
            msg = "Supplied path is not a file: {0}".format(args[0])
            logger.fatal(msg)
            raise CommandError(msg)

        digest = smhash(args[0])
        print("{0}: {1}".format(args[0], digest))

        logger.info("Archive finished")

        return
