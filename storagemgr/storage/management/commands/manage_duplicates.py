"""
Current thoughts:

* Remove by:
** Root
** Path
** File

In all cases, it is necessary to ensure that we will never remove all files
with the same hash value.
"""
import re
from os.path import isdir, abspath
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from storage.models import Hash, File
from storage.duplicates import Duplicates, Deduplicate

from logger import init_logging
logger = init_logging(__name__)



class Command(BaseCommand):
    args = ''
    help = 'Manage duplicate files'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='Load pdb and halt on startup'),
        make_option('--short_summary',
            action='store_true',
            dest='short_summary',
            default=False,
            help='Print a short summary of the duplicates'),
        make_option('--long_summary',
            action='store_true',
            dest='long_summary',
            default=False,
            help='Print a long summary of the duplicates'),
        make_option('--show_hash',
            action='store_true',
            dest='show_hash',
            default=False,
            help='Print the files for the supplied (part) hash'),
        make_option('--deduplicate',
            action='store_true',
            dest='deduplicate',
            default=False,
            help='Replace duplicates with symbolic links'),
        )

    def handle(self, *args, **options):

        if options['debug']:
            import pdb
            pdb.set_trace()

        logger.info("Manage Duplicates starting")
        
        if options['short_summary']:
            self._print_short_summary()
        if options['long_summary']:
            self._print_long_summary()
        if options['show_hash']:
            self._print_show_hash(args)
        if options['deduplicate']:
            self.deduplicate()

        logger.info("Manage Duplicates finished")

        return

    def _print_short_summary(self):
        self.duplicates = Duplicates()
        print("Grand Total: {0}\n".format(len(self.duplicates.data_frame)))
        columns = ['Root', 'Path']
        for column in columns:
            print column
            val_counts = self.duplicates.data_frame[column].value_counts()
            print val_counts
            print "\n"
        return

    def _print_long_summary(self):
        self.duplicates = Duplicates()
        ddf = self.duplicates.data_frame
        duplicate_paths = list(ddf['Path'].value_counts().index)
        for path in duplicate_paths:
            path_dups = ddf[ddf['Path'] == path]
            print(path)
            for rec in path_dups.iterrows():
                print(u"    {0:60s} {1}".format(
                    rec[1]['File'][:60], rec[1]['Hash'][:8]))
            print("\n")
        return

    def _print_show_hash(self, args):
        digest = args[0]
        files = File.objects.filter(hash__digest__startswith=digest).order_by('hash__digest', 'name')
        current_digest = ''
        for file in files:
            if file.hash.digest != current_digest:
                current_digest = file.hash.digest
                print(u"\n{0}".format(current_digest))
            print(u"    {0}".format(file.abspath))
        return
        

    def deduplicate(self):
        """Replace duplicates with symbolic links.
        
        The decision on which of the duplicates is removed is based on:
        
        - Path priority
        -- The user is asked to specify which directory takes priority.
        -- The response is stored so that the user is only asked once,
        -- all subsequent duplicates in the same pair of directories 
        -- are automatically handled.
        - If the files are in the same directory, the user is asked to choose
        """
        logger.debug("De-duplicating")
        self.duplicates = Duplicates()
        ddf = self.duplicates.data_frame
        #
        # Iterate over each hash and decide what to do
        #
        for digest in self.duplicates.data_frame['Hash'].unique():
            hash = Hash.objects.get(digest=digest)
            dedup = Deduplicate(hash, keep_callback)
            dedup.deduplicate()
        return


def keep_callback(files):
    """Ask the user which file to keep.
    Answer the index in to files."""
    for i in range(len(files)):
        print("{i}: {fn}".format(i=i, fn=files[i].abspath))
    idx = raw_input("Index to keep: ")
    idxre = re.compile('[0-9]+')
    if not idxre.match(idx):
        raise ValueError("Expected an integer number")
    idx = int(idx)
    assert idx < len(files), "Index out of range"
    return idx
