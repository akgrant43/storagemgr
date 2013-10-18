import os
import hashlib
from datetime import datetime
from os.path import exists, islink, join

from django.db import models
from django.db.models import Q

# Create your models here.

class Hash(models.Model):
    """The Hash table is a sparse list of digests of the managed files"""

    digest = models.CharField(max_length=128, unique=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now=True)

    @classmethod
    def gethash(cls, digest):
        """Answer a Hash instance for the supplied digest,
        creating if necessary"""
        qs = cls.objects.filter(digest=digest)
        assert len(qs) <= 1, "Found duplicate Hashes"
        if len(qs) == 1:
            return qs[0]
        else:
            hash = Hash(digest=digest)
            hash.save()
            return hash

    def __unicode__(self):
        return self.digest



class RootPath(models.Model):
    """Store the path of monitored folders
    
    The root path must always be stored as an absolute path."""

    path = models.CharField(max_length=4096, unique=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now=True)

    @property
    def abspath(self):
        return self.path

    def __unicode__(self):
        return self.abspath


class RelPath(models.Model):
    """Store the relative path from root to file"""
    path = models.CharField(max_length=4096, blank=True)
    root = models.ForeignKey(RootPath)
    creation_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("path", "root")

    @classmethod
    def getrelpath(cls, path, root_path=None):
        """Answer an instance of the receiver for the supplied path.
        Create if necessary.
        If the root_path of the path is known it will speed things up."""
        if root_path is None:
            # For now use a simple brute force search
            # The number of root paths is expected to be small,
            # so this won't be a huge issue
            roots = RootPath.objects.all()
            for root in roots:
                if path.startswith(root):
                    root_path = root
                    break
        assert root_path is not None, "Requested RelPath has no Root"
        if len(path) > len(root_path.path):
            rel_path_str = path[len(root_path.path)+1:]
        else:
            rel_path_str = ''
        rel_paths = RelPath.objects.filter(root=root_path,
                                           path=rel_path_str)
        assert len(rel_paths) <= 1, "Found more than one RelPath with same name"
        if len(rel_paths) == 0:
            rel_path = RelPath(root=root_path, path=rel_path_str)
            rel_path.save()
        else:
            rel_path = rel_paths[0]
        return rel_path

    @property
    def abspath(self):
        return join(self.root.abspath, self.path)

    def __unicode__(self):
        return self.abspath


class ExcludeDir(models.Model):
    """Each record is a regular expression that will be applied to the selected
    RootDir, or all directories."""
    
    regex = models.CharField(max_length=4096)
    root_path = models.ForeignKey(RootPath, null=True)

    class Meta:
        unique_together = ('regex', 'root_path')

    def __unicode__(self):
        if self.root_path:
            rp = self.root_path.abspath
        else:
            rp = "Global"
        return u"{0} ({1})".format(self.regex, rp)

class File(models.Model):
    """Store file details

    :param size:          derived from os.stat
    :param mtime:         derived from os.stat
    :param symbolic_link: True if this is a symbolic link
    :param deduped:       True if this link was created during deduplication
    :param deleted:       The date the file was noticed as deleted.
                          Multiple files can have the same abspath, 
                          all or all but one must be deleted.
    
    * File instances should only be created with their name and path.
      After that they should be responsible for updating themselves,
      i.e. use add_details() and update_details().
    * Symbolic links are stored with the digest of their original file.
    * 0 byte files have a digest of "0"
    """

    name = models.CharField(max_length=4096)
    path = models.ForeignKey(RelPath)
    hash = models.ForeignKey(Hash)
    size = models.BigIntegerField()
    mtime = models.FloatField()
    symbolic_link = models.BooleanField(default=False)
    deduped = models.BooleanField(default=False)
    deleted = models.DateTimeField(null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now=True)

    @property
    def mdatetime(self):
        return datetime.fromtimestamp(self.mtime)

    @property
    def abspath(self):
        return join(self.path.abspath, self.name)

    def os_stats(self):
        """Answer os.stats() for the receiver.
        For a symbolic link we want the stats of the link, not the target."""
        if islink(self.abspath):
            stats = os.lstat(self.abspath)
        else:
            stats = os.stat(self.abspath)
        return stats

    def os_stats_changed(self):
        """Answer a boolean indicating whether the os.stats() related metadata
        has changed, i.e. mtime & size."""
        stats = self.os_stats()
        res = self.mtime != stats.st_mtime or \
                self.size != stats.st_size
        return res

    def update_details(self):
        """Update the details of the receiver (excluding path and name)"""
        # We don't expect to update the details of deleted files
        assert self.deleted is None, \
            u"Can't update deleted file: {0}".format(self.abspath)

        # The file must be accessible
        assert exists(self.abspath), \
            u"File not accessible: {0}".format(self.abspath)

        self.symbolic_link = islink(self.abspath)
        stats = self.os_stats()
        self.mtime = stats.st_mtime
        self.size = stats.st_size
        if self.size == 0:
            digest = "0"
        else:
            hasher = hashlib.sha256()
            read_size = hasher.block_size * 1024
            with open(self.abspath, 'rb') as fp:
                while True:
                    buf = fp.read(read_size)
                    if len(buf) == 0:
                        break  
                    hasher.update(buf)
            digest = hasher.hexdigest()
        self.hash = Hash.gethash(digest)
        self.save()

    def mark_deleted(self):
        """Mark the receiver as deleted"""
        self.deleted = datetime.now()
        self.save()

    def deduplicated(self):
        """Mark the receiver as deduplicated"""
        self.symbolic_link = True
        self.deduped = True
        self.save()

    def __unicode__(self):
        return self.abspath


class PathPriority(models.Model):
    """Store the relative priority of pairs of directories.
    
    This is used by the de-duplication functionality to determine which
    files to convert to symbolic links.
    
    patha has priority over pathb."""
    
    patha = models.ForeignKey(RelPath, related_name="patha")
    pathb = models.ForeignKey(RelPath, related_name="pathb")
    creation_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['patha', 'pathb']

    def save(self):
        """Ensure that these paths aren't already paired"""
        query = Q(patha=self.patha, pathb=self.pathb) | \
                Q(patha=self.pathb, pathb=self.patha)
        existing = self.__class__.objects.filter(query)
        if existing.count() > 0:
            raise ValueError(u"Path's already prioritised: {0} and {1}"\
                .format(self.patha, self.pathb))
        super(self.__class__, self).save()

    @classmethod
    def priorities_for(cls, patha, pathb):
        """Answer the record for the supplied paths, if it exists"""
        query = Q(patha=patha, pathb=pathb) | \
                Q(patha=pathb, pathb=patha)
        records = cls.objects.filter(query)
        assert records.count() <= 1, "Found conflicting priorities"
        if records.count() == 0:
            return None
        else:
            return records[0]

    @classmethod
    def update_priorities(cls, patha, pathb):
        """Record patha as having higher priority than pathb"""
        
        # If the paths are the same, do nothing
        if patha == pathb:
            return
        

    @classmethod
    def prioritise(cls, filea, fileb):
        """Answer an integer indicating which file has priority 
        based on path priorities:
        
        1:  filea has priority
        0:  Unknown
        -1: fileb has priority
        """
        
        # If the directories are the same, no priority
        if filea.path == fileb.path:
            return 0

        priority = cls.priorities_for(filea.path, fileb.path)        
        if priority is None:
            return 0

        if filea == priority.patha:
            return 1
        elif fileb == priority.patha:
            return -1

        # How did we get here?
        raise ValueError("Priority algorithm error")
        