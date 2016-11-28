"""
Storagemgr Test settings

Tests need to be run with:

$ manage.py test storage --settings=storagemgr.settings_test
"""

from storagemgr.settings import *

LOGGING['handlers']['rotate']['filename'] = '/dev/shm/storagemgr_tests.log'

DATABASES['default'] = DATABASES['sqlitedb']
#DATABASES['default']['NAME'] = '/dev/shm/test.db'
DATABASES['default']['NAME'] = ':memory:'
del DATABASES['mysqldb']
del DATABASES['sqlitedb']

IMAGES_ARCHIVE = '/dev/shm/storagemgr'
VIDEO_ARCHIVE = '/dev/shm/storagemgr'
