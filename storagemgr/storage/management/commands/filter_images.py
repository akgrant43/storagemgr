import re
from gi.repository import GExiv2
from os import walk
from os.path import isdir, join, splitext

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from storage.models import IMAGE_TYPES

from logger import init_logging
logger = init_logging(__name__)


def get_exiv2(fn):
    try:
        img_exiv2 = GExiv2.Metadata(fn)
    # Catching every exception is really bad, but I can't catch
    # GLib.Error :-(
    except Exception as e:
    #except IOError, GLib.Error:
        msg = "GExiv2 exception on {0}, ignoring, e={1}".format(
                fn, e)
        logger.warn(msg)
        img_exiv2 = None
    return img_exiv2


class Command(BaseCommand):
    args = ''
    help = 'Find images matching the specified filters'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        make_option('--model',
            default=None,
            help='Filter on camera model (regex)'),
        )

    def handle(self, *args, **options):

        logger.info("filter_images starting")
        if options['debug']:
            import pdb
            pdb.set_trace()

        if not isdir(args[0]):
            msg = "Supplied path is not a directory: {0}".format(args[0])
            logger.fatal(msg)
            raise CommandError(msg)

        if options['model'] is None:
            msg = "model is currently the only filter and is required"
            logger.fatal(msg)
            raise CommandError(msg)
        model_re = re.compile(options['model'])
        for root, dirs, files in walk(args[0]):
            for fn in files:
                if splitext(fn)[1].lower() in IMAGE_TYPES:
                    fnpath = join(root, fn)
                    #print "Processing: {0}".format(fnpath)
                    model = None
                    img_exiv2 = get_exiv2(fnpath)
                    if img_exiv2 is None:
                        continue
                    if model_re.search(img_exiv2.get('Exif.Image.Make') or ''):
                        model = img_exiv2.get('Exif.Image.Make')
                    if model_re.search(img_exiv2.get('Exif.Image.Model') or ''):
                        model = img_exiv2.get('Exif.Image.Model')
                    if model is not None:
                        print fnpath

        logger.info("filter_images finished")

        return
