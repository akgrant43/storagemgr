"""
Storagemgr Test settings
"""

from storagemgr.settings import *

DATABASES['default'] = DATABASES['sqlitedb']
#DATABASES['default']['NAME'] = '/run/shm/test.db'
DATABASES['default']['NAME'] = ':memory:'
del DATABASES['mysqldb']
del DATABASES['sqlitedb']

IMAGES_ARCHIVE = '/run/shm/storagemgr'
VIDEO_ARCHIVE = '/run/shm/storagemgr'
