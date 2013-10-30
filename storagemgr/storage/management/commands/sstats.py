from os.path import isdir, abspath
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from storage.models import File, Keyword, RootPath

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Print basic stats'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        )

    def handle(self, *args, **options):

        if options['debug']:
            import pdb
            pdb.set_trace()

        logger.info("sstats starting")
        print("Root Paths:")
        print("===========")
        for p in RootPath.objects.all():
            print("    {0}".format(p.path))
        print("\n\n")
        print("Keywords:")
        print("=========")
        for kw in Keyword.objects.all():
            print("    {0}".format(kw.name))
        print("\n\n")
        print("File Count: {0}".format(File.objects.count()))
        logger.info("sstats finished")

        return
