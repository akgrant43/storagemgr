import os
import shutil
import pandas as pd
from os.path import join
from copy import copy

from storage.models import Hash, RootPath, RelPath, File
from storage.models import PathPriority

from logger import init_logging
logger = init_logging(__name__)

MBytes = 1024.0 * 1024.0

class Duplicates(object):
    """Report on duplicate files"""
    
    def __init__(self):
        self.hash = None
        self.root_path = None
        self.path = None
        self.file = None

    def duplicates(self):
        """Answer the set of duplicates"""
        ic = self.file['hash'].value_counts()
        dups_digest = ic[ic>1]
        duplicates = copy(self)
        duplicates.file = self.file.ix[dups_digest.index]
        return duplicates

    def uniques(self):
        """Answer the set of uniques"""
        ic = self.file['hash'].value_counts()
        dups_digest = ic[ic==1]
        uniques = copy(self)
        uniques.file = self.file.ix[dups_digest.index]
        return uniques

    def for_path(self, path):
        """Answer the subset of entries matching path"""
        mask = self.path['Path'].apply(lambda x: x.startswith(path))
        paths = self.path[mask]
        res = copy(self)
        path_ids = paths.index
        files_mask = self.file['path'].apply(lambda x: x in path_ids)
        res.path = paths
        res.file = self.file[files_mask]
        return res

    def store(self, fn):
        store = pd.HDFStore(fn)
        store['file'] = self.file
        store['path'] = self.path
        store['root_path'] = self.root_path
        store['hash'] = self.hash
        store.close()

    @classmethod
    def load_from_db(cls, *args, **kwargs):
        dup = cls()
        hash = pd.DataFrame.from_records(Hash.objects.values('id', 'digest'))
        dup.hash = hash.set_index('id')
        root_path = pd.DataFrame.from_records(RootPath.objects.values('id', 'path'))
        dup.root_path = root_path.set_index('id')
        
        ids = []
        roots = []
        pths = []
        for path in RelPath.objects.all():
            ids.append(path.id)
            roots.append(path.root_id)
            pths.append(path.abspath)
        dup.path = pd.DataFrame({'Root': roots, 'Path': pths}, index=ids)

        index = ['id', 'hash', 'path', 'name', 'size', 'mtime',
                 'symbolic_link', 'deduped', 'deleted']
        files = pd.DataFrame.from_records(File.objects.values(*index))
        dup.file = files.set_index('id')
        return dup

    @classmethod
    def load_from_store(cls, fn):
        store = pd.HDFStore(fn)
        dup = cls()
        dup.hash = store['hash']
        dup.root_path = store['root_path']
        dup.path = store['path']
        dup.file = store['file'] 
        store.close()
        return dup


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
        assert self.have_tmp_space(), \
            u"Insufficient free space in {0}".format(settings.TMP_PATH)
        # Move from_file to TMP_PATH
        tmp_prefix = join(settings.TMP_PATH, 'storagemgr')
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

    def have_tmp_space(self):
        """Answer a boolean indicating whether there is sufficient free space
        on the tmp drive to continue deduplication."""
        
        stats = os.statvfs(settings.TMP_PATH)
        free = float(stats.f_bavail) * float(stats.f_frsize) / MBytes
        return settings.TMP_MIN_SPACE > free
