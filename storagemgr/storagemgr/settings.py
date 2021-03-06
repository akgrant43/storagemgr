# Django settings for storagemgr project.
import os
from os.path import abspath
from os.path import join

PROJECT_PATH = abspath(os.path.split(__file__)[0])
PROJECT_DIR = os.path.dirname(PROJECT_PATH)
DB_PATH = os.environ.get('STORAGEMGR_DB_PATH',
                        '/mnt/daa/data1/akg/storagemgr')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s %(process)d %(thread)d %(message)s'
            },
        'simple': {
            'format': '%(levelname)s: %(message)s'
            },
        },
    'filters': {
        },
    'handlers': {
        'rotate': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': join(PROJECT_DIR, 'storagemgr.log'),
            'maxBytes': 10000000,
            'backupCount': 5
            },
        'console':{
            'level':'WARN',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
            },
        },
    'loggers': {
        'django': {
            'handlers':['rotate'],
            'propagate': True,
            'level':'WARN',
            },
        },
    'root' : {
        'handlers' : ['rotate', 'console'],
        'level' : 'DEBUG',
        },
}


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Alistair Grant', 'akgrant@gmail.com'),
)

DATABASES = {
    'mysqldb': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'daa',                      # Or path to database file if using sqlite3.
        'USER': 'smgr',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB, SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED'
        }
    },
    'sqlitedb': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': join(DB_PATH, 'storagemgr.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}
DATABASES['default'] = DATABASES['mysqldb']

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
#TIME_ZONE = 'Europe/Prague'
TIME_ZONE = 'Australia/Sydney'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$vb=@*h9)=jyxdofue7y!3v-2u_y(40_cig_jn36wn#@&s*)p5'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'storagemgr.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'storagemgr.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'django_extensions',
    'storage',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Specify the location and minimum required space for deduplication backup (MB)
TMP_PATH = '/tmp'
TMP_MIN_SPACE = 100 # MB

IMAGES_ARCHIVE = '/mnt/daa/data1/Photos'
VIDEO_ARCHIVE = '/mnt/daa/data1/Photos'
