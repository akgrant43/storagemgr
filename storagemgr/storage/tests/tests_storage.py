"""
Test the core storagemgr functionality - scanning and maintaing the archive
"""
from shutil import copy2, rmtree
from os.path import isdir, join
from os import makedirs, remove

from django.conf import settings
from django.test import TestCase

from storage.models import RootPath, File
from storage.scan import QuickScan

class StorageTests(TestCase):
    
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

    def test_initial_scan(self):
        """Confirm that the setUp produced the expected environment"""
        self.assertEqual(File.objects.all().count(), 2)
        i1 = File.objects.get(name='image1.png')
        self.assertEqual(i1.hash.digest,
                         'a9a008968f02ce2ee596052cb7212734b8be932f0df26d2e5052401b07076bf1')
        return


    def test_delete_and_rescan(self):
        """Check:
        1. Deleted file is correctly marked as such.
        2. Recovered and rescanned produces new entry.
        """
        # Delete image2, rescan and confirm deleted
        remove(self.image2)
        scanner = QuickScan()
        scanner.scan()
        i2 = File.objects.get(name='image2.png')
        self.assertTrue(i2.deleted, "Expected image2.png to be deleted")
        
        # Recover file, rescan, and check for undeleted entry
        copy2(self.image2_src, self.rootdir)
        scanner.scan()
        self.assertEqual(File.objects.filter(name='image2.png').count(), 2)
        self.assertEqual(File.objects.filter(
                            name='image2.png', deleted__isnull=True).count(), 1)
        return
