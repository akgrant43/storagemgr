"""
Module: archiver

Archive files chronologically using: YYYY/MMmmm

The date is taken from internal metadata for known file types, otherwise from 
the file modification date at time of archive.
"""

import shutil
import pyexiv2
from os import walk, makedirs
from os.path import join, splitext, getmtime, isdir, isfile
from datetime import datetime
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata

from storage.smhash import smhash
from storage.models import Hash, RootPath, RelPath, File, Keyword

from logger import init_logging
logger = init_logging(__name__)

class UnknownFormat(Exception):
    pass


class Archiver(object):
    """Archive the supplied directory"""
    
    def __init__(self, source, destination, descend=True):
        self.source = source
        self.destination = destination
        self.root_path = RootPath.getrootpath(destination)
        assert self.root_path is not None, "No root for requested destination"
        self.descend = descend
        return

    def archive(self):
        logger.info("Archiving from {0} to {1}".format(
            self.source, self.destination))
        for root, folders, filenames in walk(self.source):
            self.archive_files(filenames, root)
        return

    def archive_files(self, filenames, root):
        """Archive all the files in the supplied hierarchy"""
        tmp_root = RootPath(path=root)
        tmp_path = RelPath(path=root, root=tmp_root)
        for fname in filenames:
            fn = join(root, fname)
            if not self.archive_file(fn):
                logger.debug("skipped {0}".format(fn))
                continue
            tmp_file = File(path=tmp_path, name=fname)
            tmp_file.get_details()
            matching = tmp_file.matching_files()
            if len(matching) == 0:
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
                shutil.copy2(fn, new_file.abspath)
                new_file.update_details()
                logger.info("added {0} as {1} ({2})".format(
                            fn,
                            new_file.name,
                            new_file.hash.digest))
            else:
                # Merge keywords from the new file
                keywords = tmp_file.file_keywords()
                if len(keywords) > 0:
                    for existing_file in matching:
                        logger.info("updating {0} from matching file {1}".format(
                            existing_file, fname))
                        existing_keywords = existing_file.keyword_set.all()
                        new_keywords = set(keywords) - set(existing_keywords)
                        logger.info("Adding keywords {0} to {1}".format(
                            new_keywords, existing_file))
                        for kw in new_keywords:
                            Keyword.get_or_add(kw).files.add(existing_file)
                else:
                    logger.info("{0} matches {1}".format(fname, matching))
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

    def __init__(self, source, destination, descend=True):
        self.image_types = ['.jpg', '.jpeg', '.tif', '.tiff', '.raw', '.png']
        super(ImageArchiver, self).__init__(source, destination, descend)
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
            metadata = pyexiv2.ImageMetadata(fnpath)
            metadata.read()
            if 'Exif.Photo.DateTimeOriginal' in metadata.exif_keys:
                fdate = metadata['Exif.Photo.DateTimeOriginal'].value
            elif 'Exif.Image.DateTime' in metadata.exif_keys:
                fdate = metadata['Exif.Image.DateTime'].value
            # The image can contain an invalid value, in which case the
            # date will come back as a string - which we don't know
            # what to do with, so make None again
            if not isinstance(fdate, datetime):
                fdate = None
        except IOError as e:
            # If it isn't a recognised format, don't worry...
            msg = "pyexiv2 exception on {0}, ignoring, e={1}".format(
                    fnpath, e)
            logger.warn(msg)
            pass
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

    def __init__(self, source, destination, descend=True):
        self.archive_types = ['.mov', '.mpg', '.mp4', '.m4v', '.mpeg']
        super(VideoArchiver, self).__init__(source, destination, descend)
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
        fdate = None
        try:
            ufnpath = unicode(fnpath, 'utf-8')
            parser = createParser(ufnpath)
            if parser is None:
                raise UnknownFormat("Can't parse {0}".format(fnpath))
            metadata = extractMetadata(parser, 0.0)
            fdate = metadata.get('creation_date')
            if fdate.year < 1972:
                # It isn't valid
                fdate = None
        except (ValueError, IOError, AttributeError, UnknownFormat) as e:
            # If it isn't a recognised format, don't worry...
            msg = "hachoir exception on {0}, ignoring, e={1}".format(
                    fnpath, e)
            logger.warn(msg)
            pass
        if fdate is None:
            fdate = super(VideoArchiver, self).date(fnpath)
        return fdate

    def new_fn(self, full_path, fdate, filename):
        """Answer the file format: VID-YYYYMMDD-HHMM-u.type"""
        ftype = splitext(filename)[1].lower()
        newname = "VID-" + fdate.strftime("%Y%m%d-%H%M%S-") + \
                    str(fdate.microsecond) + ftype
        return newname
