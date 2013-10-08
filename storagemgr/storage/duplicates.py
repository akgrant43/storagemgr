import os
import shutil
import pandas as pd
from os.path import join

from storage.models import Hash, RootPath, RelPath, File
from storage.models import PathPriority

from logger import init_logging
logger = init_logging(__name__)


class Duplicates(object):
    """Report on duplicate files"""
    
    def __init__(self):
        self.data_frame = self._data_frame()

    def _data_frame(self):
        """Answer the pandas dataframe with all duplicates
        
        Columns:
        - Hash
        - Root
        - Path
        - File"""

        index = ['Hash', 'Root', 'Path', 'File']
        df = pd.DataFrame(index=index)
        i = 0
        for hash in Hash.objects.all():
            file_set = File.objects.filter(hash=hash, symbolic_link=False)
            if file_set.count() > 1:
                for file in file_set.all():
                    s = pd.Series([hash.digest,
                                   file.path.root.path,
                                   file.path.abspath,
                                   file.name],
                                  index=df.index)
                    df[i] = s
                    i += 1
        return df.T


class Deduplicate(object):
    """Do the work of deciding which files to remove for the supplied Hash
    and setting up the symbolic links."""
    
    def __init__(self, hash, keep_callback):
        self.hash = hash
        self.keep_callback = keep_callback


    def deduplicate(self):
        """Replace duplicates with symbolic links.
        
        Two-passes:
        1. If the duplicates are in different directories, and the directories
           have already been prioritised, automatically deal with it.
           If there are still duplicates...
        2. Request the file to be kept through the call back and then deal with
           the remaining duplicates"""
        
        #
        # There's bound to be a more clever way to do this, however:
        #
        # 1. Repeatedly iterate over the set of files removing lower priority
        #    files where there is already a priority set
        #    If there are still duplicates...
        # 2. Ask for a winner when no more files can be removed automatically
        #
        files = list(File.objects.filter(hash=self.hash, symbolic_link=False))
        
        if len(files) <= 1:
            # Nothing to do
            return

        # Really want do..until, initialise exit condition
        files_length = len(files) + 1
        # Loop until nothing else can be removed
        while files_length != len(files):
            files_length = len(files)
            for i in range(len(files)-1):
                file_i = files[i]
                for j in range(1, len(files)):
                    file_j = files[j]
                    priority = PathPriority.prioritise(file_i, file_j)
                    if priority == 1:
                        # file_i has priority, link file_j to it
                        files.remove(file_j)
                        self.link(file_j, file_i)
                        break
                    elif priority == -1:
                        # file j has priority, linke file_i to it
                        files.remove(file_i)
                        self.link(file_i, file_j)
                        break
                    else:
                        assert priority == 0, "Unexpected file priority value"
                else:
                    continue
                break
        
        #
        # If there are still duplicates, ask for the winner
        #
        if len(files) > 1:
            keep_index = self.keep_callback(files)
            keep = files[keep_index]
            files.remove(keep)
            for file in files:
                PathPriority.update_priorities(keep.path, file.path)
                self.link(file, keep)

        return


    def link(self, from_file, to_file):
        """Remove from_file and replace with a symbolic link to to_file.
        
        This will remove from_file from the database
        (since it no longer exists)"""

        logger.info(u"Deduplicate: Linking {0} to {1}".format(
                    from_file.abspath, to_file.abspath))
        # Move from_file to /tmp
        tmp_prefix = '/tmp/storagemgr'
        try:
            tmp_path = tmp_prefix+from_file.path.abspath
            os.makedirs(tmp_path)
        except os.error:
            # Ignore failures,
            # it's probably because the tmp directory already exists,
            # and if not, it will be caught below in the rename
            pass
        to_path = tmp_prefix+from_file.abspath
        shutil.copy(from_file.abspath, to_path)
        os.remove(from_file.abspath)
    
        # Create the symbolic link
        os.symlink(to_file.abspath, from_file.abspath)

        # Mark the old file deduplicated
        from_file.deduplicated()

        return
