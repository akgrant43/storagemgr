"""
Storagemgr Test settings
"""

from storagemgr.settings import *

DATABASES['default'] = DATABASES['sqlitedb']
DATABASES['default']['NAME'] = '/run/shm/test.db'

IMAGES_ARCHIVE = '/run/shm/storagemgr'
VIDEO_ARCHIVE = '/run/shm/storagemgr'
