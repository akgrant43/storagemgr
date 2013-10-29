from os.path import isdir, abspath
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from storage.scan import QuickScan

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = '<root path...>'
    help = 'Scan the managed directories for changes'
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

        logger.info("Quick Scan starting")
        for rp in args:
            scan = QuickScan(rp)
            print("Scanning: {0}".format(scan.root_paths))
            scan.scan()
        logger.info("Quick Scan finished")

        return
