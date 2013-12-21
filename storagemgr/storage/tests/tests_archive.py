"""
Test the archiver functionality.
"""
from shutil import copy2, rmtree
from os.path import isdir, isfile, join
from os import makedirs, remove

from django.conf import settings
from django.test import TestCase

from storage.models import RootPath, RelPath, File, Hash
from storage.scan import QuickScan
from storage.archiver import ImageArchiver, VideoArchiver


class ArchiveTests(TestCase):

    def setUp(self):
        # Get tmp directory
        tmpdirs = ['/run/shm', '/tmp']
        self.tmpdir = None
        for d in tmpdirs:
            if isdir(d):
                self.tmpdir = d
                break
        self.assertNotEqual(self.tmpdir, None, 
            msg="Unable to find temporary directory")
        
        # Create initial directories to manage
        self.rootdir = join(self.tmpdir, 'storagemgr_tests')
        if isdir(self.rootdir):
            # Delete the directory and start again
            rmtree(self.rootdir)
        makedirs(self.rootdir)
        self.test_data = join(settings.PROJECT_DIR, 'storage', 'test_data')

        # Copy initial files in
        self.image1_src = join(self.test_data, "image1.png")
        copy2(self.image1_src, self.rootdir)
        self.image2_src = join(self.test_data, "image2.png")
        copy2(self.image2_src, self.rootdir)
        self.image2 = join(self.rootdir, "image2.png")

        # Initial DB population
        self.rootpath = RootPath(path=self.rootdir)
        self.rootpath.save()
        scanner = QuickScan()
        scanner.scan()

        return

    def test_initial_archive(self):
        """Archive the first test directory and ensure file is added"""
        archive1 = join(self.test_data, "archive1")
        archiver = ImageArchiver(archive1, self.rootdir)
        archiver.archive()
        self.assertEqual(File.objects.count(), 3)
        i3 = File.objects.get(name='IMG-20131214-084900-0.png')
        self.assertEqual(i3.hash.digest,
            'e60698d93e7b7f6955efce729a8fbab2399cbd13fa7b13ac3c2bdc7ffb419ef4')
        return


    def test_archive_deleted(self):
        """Check:
        1. Archiving a deleted file doesn't re-add it to the archive
        """
        # Delete image2, rescan and confirm deleted
        remove(self.image2)
        scanner = QuickScan()
        scanner.scan()
        i2 = File.objects.get(name='image2.png')
        self.assertTrue(i2.deleted, "Expected image2.png to be deleted")
        
        # Archive archive2, which contains a copy of image2,
        # which should not be archived
        archive2 = join(self.test_data, "archive2")
        archiver = ImageArchiver(archive2, self.rootdir)
        archiver.archive()
        # There should still be three objects
        self.assertEqual(File.objects.count(), 2)
        # The hash of image2 should only have the deleted file
        fhash = Hash.objects.get(
            digest='245346fa2da665e78e4e36994bb9f0bd654ad8ef4d2f4622fca361280935fd8f')
        files = File.objects.filter(hash=fhash)
        self.assertEqual(files.count(), 1)
        self.assertIsNotNone(files[0].deleted)
        return


    def test_rearchive(self):
        """Check:
        1. Re-archiving the same directory doesn't modify the database.
        """
        archive1 = join(self.test_data, "archive1")
        archiver = ImageArchiver(archive1, self.rootdir)
        archiver.archive()
        files = File.objects.all()
        self.assertEqual(files.count(), 3)
        orig_dates = set([x.mod_date for x in files])
        archiver.archive()
        files = File.objects.all()
        new_dates = set([x.mod_date for x in files])
        self.assertEqual(orig_dates, new_dates)
        return


    def test_same_date(self):
        """Check:
        1. Two files with the same date (but different hash) are given
           unique names.
        """

        # Archive image3.png
        archive1 = join(self.test_data, "archive1")
        archiver = ImageArchiver(archive1, self.rootdir)
        archiver.archive()
        # Archive image4.png
        archive3 = join(self.test_data, "archive3")
        archiver = ImageArchiver(archive3, self.rootdir)
        archiver.archive()

        i3 = File.objects.get(name='IMG-20131214-084900-0.png')
        i4 = File.objects.get(name='IMG-20131214-084900-0-1.png')
        self.assertEqual(i3.date, i4.date)
        return


    def test_no_overwrite(self):
        """Check:
        1. The system doesn't overwrite a file with the target name.
        """
        dest_dir = join(self.rootdir, "2013", "12Dec") 
        makedirs(dest_dir)
        copy2(join(self.test_data, "archive1", "image3.png"),
              join(dest_dir, "IMG-20131214-084900-0.png"))
        archive1 = join(self.test_data, "archive1")
        archiver = ImageArchiver(archive1, self.rootdir)
        archiver.archive()
        self.assertTrue(isfile(join(dest_dir, "IMG-20131214-084900-0-1.png")),
                        "Didn't find IMG-20131214-084900-0-1.png")
        return
