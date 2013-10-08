from os.path import isdir, abspath
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from storage.models import RootPath, ExcludeDir

from logger import init_logging
logger = init_logging(__name__)

COMMANDS = ['add', 'remove', 'exclude_dir']


class Command(BaseCommand):
    args = ''
    help = 'Manage root folders'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        )

    def handle(self, *args, **options):
        command = args[0].lower()

        if options['debug']:
            import pdb
            pdb.set_trace()

        if command not in COMMANDS:
            msg = 'Unknown command: {0}'.format(command)
            logger.fatal(msg)
            raise CommandError(msg)

        if command == 'add':
            self.add(args, options)
        if command == 'remove':
            self.remove(args, options)
        if command == 'exclude_dir':
            self.exclude_dir(args, options)

        return

    def add(self, args, options):
        rpath = args[1]
        
        if not isdir(rpath):
            msg = 'Not a valid path: {0}'.format(rpath)
            logger.fatal(msg)
            raise CommandError(msg)
        
        path = abspath(rpath)
        new_root = RootPath(path=path)
        new_root.save()
        msg = 'Added new path: {0}'.format(path)
        print msg
        logger.info(msg)
        return

    def exclude_dir(self, args, options):
        regex = args[1]
        root_path = None
        if len(args) > 2:
            root_path = RootPath.objects.get(path=args[2])

        new_exclude = ExcludeDir(regex=regex, root_path=root_path)
        new_exclude.save()
        msg = u'Added new excluded directory: {0}'.format(regex)
        print msg
        logger.info(msg)
        return
