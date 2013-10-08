import os
import re
from os.path import islink

from django.db.models import Q

from storage.models import Hash, RootPath, RelPath, File, ExcludeDir

from logger import init_logging
logger = init_logging(__name__)

class Scan(object):
    """Abstract functionality for scanning folders.
    
    Either FullScan or QuickScan should be instantiated."""
    
    def __init__(self):
        self.root_paths = RootPath.objects.all()

    def scan(self):
        """Scan each root path in turn and update the database"""
        # Iterate over each of the managed root paths
        for root_path in self.root_paths:
            # Build the list of regexe's
            regexes = []
            query = Q(root_path=root_path) | Q(root_path=None)
            for rec in ExcludeDir.objects.filter(query):
                regexes.append(re.compile(rec.regex))

            # Iterate over each of the files in the current root path
            for root, dirs, files in os.walk(root_path.abspath):
                #
                # Get the path to the current directory
                #
                rel_path = RelPath.getrelpath(root, root_path=root_path)
                
                #
                # Continue if directory is excluded
                #
                skip = False
                i = 0
                while (i < len(regexes)) and not skip:
                    if regexes[i].search(rel_path.abspath):
                        logger.debug(u"Skipping: {0}".format(rel_path.abspath))
                        skip=True
                    i += 1
                if skip:
                    continue

                #
                # Get the list of known files so we can remove any
                # that have been deleted
                #
                known_files = list(File.objects.filter(path=rel_path))
                
                #
                # Iterate over the files in the current directory and ensure
                # the hash is up to date (QuickScan or FullScan).
                # Remove each file from the list of known files on the way.
                #
                for fname in files:
                    file = self.file(rel_path, fname)
                    if file is None:
                        self.add_file(rel_path, fname)
                    else:
                        known_files.remove(file)
                        if self.needs_rehash(file):
                            self.update_file(file)
                        else:
                            logger.debug(u"No change: {0}".format(file.abspath))
                
                #
                # What's left in known_files has been deleted
                # Remove from db
                #
                for file in known_files:
                    logger.debug(u"Removing from known_files: {0}".format(file.abspath))
                    file.mark_deleted()

    def file(self, rel_path, fname):
        """Answer the File object if present or None."""

        files = File.objects.filter(path=rel_path, name=fname, deleted=None)
        assert len(files) <= 1, "Found more than one matching file"
        if len(files) == 0:
            return None
        else:
            return files[0]

    def add_file(self, rel_path, fname):
        """Add the supplied fname to the db"""
        logger.debug(u"Adding: {0}".format(fname))
        file = File(path=rel_path, name=fname)
        file.update_details()
        return

    def update_file(self, file):
        logger.debug(u"Updating: {0}".format(file.abspath))
        file.update_details()
        return


class QuickScan(Scan):
    """QuickScan assumes that a file with the same mtime and size hasn't
    changed, so doesn't require its hash to be recalculated."""
    
    def needs_rehash(self, file):
        return file.os_stats_changed()


class FullScan(Scan):
    """FullScan rehashes every file, regardless of whether it has been
    changed or not"""

    def needs_rehash(self, file):
        return True
