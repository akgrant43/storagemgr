"""
Module: archiver

Archive files chronologically using: YYYY/MMmmm

The date is taken from internal metadata for known file types, otherwise from 
the file modification date at time of archive.
"""

import shutil
from gi.repository import GExiv2
from os import walk, makedirs, stat
from os.path import join, splitext, getmtime, isdir, isfile
from datetime import datetime

from storage.smhash import smhash
from storage.mediainfo import MediaInfo
from storage.models import Hash, RootPath, RelPath, File, Keyword, IMAGE_TYPES

from logger import init_logging
logger = init_logging(__name__)

class UnknownFormat(Exception):
    pass


class Archiver(object):
    """Archive the supplied directory"""
    
    def __init__(self, source, destination, descend=True, break_on_add=False):
        self.source = source
        self.destination = destination
        self.root_path = RootPath.getrootpath(destination)
        assert self.root_path is not None, "No root for requested destination"
        self.descend = descend
        self.break_on_add = break_on_add
        return

    def archive(self):
        logger.info("Archiving from {0} to {1}".format(
            self.source, self.destination))
        for root, folders, filenames in walk(self.source):
            self.archive_files(filenames, root)
        return

    def archive_files(self, filenames, root):
        """Archive all the files in the supplied hierarchy"""
        #import pdb; pdb.set_trace()
        tmp_root = RootPath(path=root)
        tmp_path = RelPath(path='', root=tmp_root)
        for fname in filenames:
            fn = join(root, fname)
            if not self.archive_file(fn):
                logger.debug("skipped {0}".format(fn))
                continue
            tmp_file = File(path=tmp_path, name=fname)
            tmp_file.get_details()
            matching = tmp_file.matching_files()
            if len(matching) == 0:
                if self.break_on_add:
                    import pdb; pdb.set_trace()
                # Add the file to the archive
                fdate = self.date(fn)
                newfn = self.new_fn(fn, fdate, fname)
                dest = join(self.destination,
                            fdate.strftime("%Y"),
                            fdate.strftime("%m%b"))
                relpath = RelPath.getrelpath(dest, self.root_path)
                if not isdir(relpath.abspath):
                    makedirs(relpath.abspath)
                newfn = self.avoid_clash(newfn, relpath)
                new_file = File(path=relpath, name=newfn)
                if isfile(new_file.abspath):
                    # This should never happen
                    raise ValueError("destination already exists: {0}".format(
                        new_file))
                #shutil.copy2(fn, new_file.abspath)
                self.copy_file(fn, new_file)
                new_file.update_details()
                logger.info("added {0} as {1} ({2})".format(
                            fn,
                            new_file.name,
                            new_file.hash.digest))
            else:
                logger.info("{0} matches {1}".format(fname, matching))
                # Merge keywords from the new file
                #import pdb; pdb.set_trace()
                keywords = set(tmp_file.file_keywords())
                if len(keywords) > 0:
                    for existing_file in matching:
                        logger.info("updating {0} from matching file {1}".format(
                            existing_file, fname))
                        existing_keywords = set(
                            [x.name for x in existing_file.keyword_set.all()])
                        new_keywords = keywords - existing_keywords
                        logger.info("Adding keywords {0} to {1}".format(
                            new_keywords, existing_file))
                        # If there are new keywords, write them to the db and
                        # back to the file
                        if len(new_keywords) > 0:
                            # Write the keywords to the database
                            for kw in new_keywords:
                                Keyword.get_or_add(kw).files.add(existing_file)
                            # Write the keywords to the archived image
                            all_keywords = list(keywords.union(existing_keywords))
                            img_exiv2 = existing_file.file_exiv2()
                            img_exiv2.set_tag_multiple(
                                'Iptc.Application2.Keywords', list(all_keywords))
                            img_exiv2.save_file()
        return

    def copy_file(self, from_fn, to_file):
        """Copy from_fn to the file pointed to by to_file,
        and validate the results"""
        from_stats = stat(from_fn)
        from_size = from_stats.st_size
        if from_size == 0:
            # Should never get here
            msg = "Source file has 0 bytes: {0}".format(from_fn)
            logger.fatal(msg)
            import pdb; pdb.set_trace()
        shutil.copy2(from_fn, to_file.abspath)
        #
        # Copy validation since we've seen some 0 length files.
        #
        # Confirm file size
        to_stats = stat(to_file.abspath)
        to_size = to_stats.st_size
        if to_size == 0:
            # Should never get here
            msg = "Copied file has 0 bytes: {0}".format(to_file.abspath)
            logger.fatal(msg)
            import pdb; pdb.set_trace()
        if to_size != from_size:
            # Should never get here
            msg = "Copied file sizes don't match: {0} and {1}".format(
                from_fn, to_file.abspath)
            logger.fatal(msg)
            import pdb; pdb.set_trace()
        # Get the mtime, we don't care about microsecond differences
        # as shutil.copy2 doesn't seem to copy microseconds
        from_mtime = datetime.fromtimestamp(from_stats.st_mtime).replace(microsecond=0)
        to_mtime = datetime.fromtimestamp(to_stats.st_mtime).replace(microsecond=0)
        if from_mtime != to_mtime:
            # Should never get here
            msg = "Copied file dates don't match: {0} and {1}".format(
                from_fn, to_file.abspath)
            logger.fatal(msg)
            import pdb; pdb.set_trace()
        return
        
    def date(self, fnpath):
        """Answer the date for the supplied filename.
        By default, use the modified time."""
        mtime = getmtime(fnpath)
        fdate = datetime.fromtimestamp(mtime)
        return fdate
    
    def new_fn(self, full_path, fdate, filename):
        """Answer the filename to use in the archive.
        By default, use the same name."""
        return filename

    def archive_file(self, path):
        """Answer a boolean indicating whether the supplied file is a 
        candidate for archiving.
        By default, all files are archived.  Sub-classes may restrict based on
        filename, etc."""
        return True
        
    def avoid_clash(self, filename, relpath):
        """Ensure that the supplied filename doesn't exist in the target
        directory."""
        newname = filename
        dest = relpath.abspath
        newp = join(dest, newname)
        if isfile(newp):
            logger.info("avoiding name clash for {0}".format(newname))
            num = 1
            name, typ = splitext(newname)
            while isfile(newp):
                newname = "{0}-{1}{2}".format(name, num, typ)
                newp = join(dest, newname)
                num += 1
        return newname



class ImageArchiver(Archiver):
    """Archive image files from the supplied hierarchy"""

    def __init__(self, source, destination, descend=True, break_on_add=False):
        self.image_types = IMAGE_TYPES
        super(ImageArchiver, self).__init__(source, destination, descend, break_on_add)
        return

    def archive_file(self, path):
        """Answer a boolean indicating whether the supplied file is a 
        candidate for archiving.
        Don't archive files that don't have a known image extension."""
        ftype = splitext(path)[1].lower()
        if ftype not in self.image_types:
            logger.debug("Skipping non-image type: {0}".format(path))
            return False
        return super(ImageArchiver, self).archive_file(path)

    def date(self, fnpath):
        """Answer the date for the supplied filename.
        Use the image metadata if available, otherwise the default."""
        fdate = None
        try:
            metadata = GExiv2.Metadata(fnpath)
            if 'Exif.Photo.DateTimeOriginal' in metadata:
                fdate = metadata['Exif.Photo.DateTimeOriginal']
            elif 'Exif.Image.DateTime' in metadata:
                fdate = metadata['Exif.Image.DateTime']
        #except IOError as e:
        except Exception as e:
            msg = "Archiver.date() exception on {0}, ignoring, e={1}".format(
                    fnpath, e)
            logger.warn(msg)
            fdate = None
        if fdate is not None:
            if len(fdate) != 19:
                msg = "Ignoring unrecognised date format: {0}".format(fdate)
                logger.debug(msg)
                fdate = None
                import pdb; pdb.set_trace()
            else:
                fdate = datetime.strptime(fdate, "%Y:%m:%d %H:%M:%S")
        if fdate is None:
            fdate = super(ImageArchiver, self).date(fnpath)
        return fdate

    def new_fn(self, full_path, fdate, filename):
        """Answer the file format: IMG-YYYYMMDD-HHMM-u.type"""
        ftype = splitext(filename)[1].lower()
        newname = "IMG-" + fdate.strftime("%Y%m%d-%H%M%S-") + \
                    str(fdate.microsecond) + ftype
        return newname



class VideoArchiver(Archiver):
    """Archive video files from the supplied hierarchy"""

    def __init__(self, source, destination, descend=True, break_on_add=False):
        self.archive_types = ['.mov', '.mpg', '.mp4', '.m4v', '.mpeg']
        super(VideoArchiver, self).__init__(source, destination, descend, break_on_add)
        return

    def archive_file(self, path):
        """Answer a boolean indicating whether the supplied file is a 
        candidate for archiving.
        Don't archive files that don't have a known video extension."""
        ftype = splitext(path)[1].lower()
        if ftype not in self.archive_types:
            logger.debug("Skipping non-video type: {0}".format(path))
            return False
        return super(VideoArchiver, self).archive_file(path)

    def date(self, fnpath):
        """Answer the date for the supplied filename.
        Use the video metadata if available, otherwise the default."""
        mediainfo = MediaInfo(fnpath)
        fdate = mediainfo.earliest_date()
        if fdate is None:
            fdate = super(VideoArchiver, self).date(fnpath)
        return fdate

    def new_fn(self, full_path, fdate, filename):
        """Answer the file format: VID-YYYYMMDD-HHMM-u.type"""
        ftype = splitext(filename)[1].lower()
        newname = "VID-" + fdate.strftime("%Y%m%d-%H%M%S-") + \
                    str(fdate.microsecond) + ftype
        return newname
