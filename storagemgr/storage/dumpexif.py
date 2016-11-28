#!/usr/bin/env python
"""Dump EXIF data using PIL and pyexiv2 (just for debugging)"""


import argparse
import logging
import logging.config

import gi
gi.require_version('GExiv2', '0.10')

from os.path import join
from PIL import Image
from gi.repository import GExiv2
from PIL.ExifTags import TAGS
#import pyexiv2

LOG_DIR = '/dev/shm/'
TMP_DIR = '/dev/shm/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'rotate': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': join(LOG_DIR, 'imagetags.log'),
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
        'pmlib': {
            'handlers' : ['rotate', 'console'],
            'propagate' : False,
            'level' : 'DEBUG',
        },
    },
    'root' : {
        'handlers' : ['rotate', 'console'],
        'level' : 'DEBUG',
    }
}

PIL_TAGS = ['Make', 'Model', 'ExifImageWidth', 'ExifImageHeight',
    'UserComment', 'ExposureTime', 'DateTime', 'ISOSpeedRatings',
    'FocalLength', 'Software', 'MaxApertureValue']

GEXIV2_TAGS = []

def main():
    parser = argparse.ArgumentParser(description='Print image tags')
    parser.add_argument('--debug', dest='debug', action='store_true',
            default=False,
            help='Load pdb and halt')
    parser.add_argument('-v', dest='verbose', action='count',
            help='Increase logging from WARN to INFO then DEBUG (multiple instances)')
    parser.add_argument('--all', action='store_true',
            default=False,
            help='Print all tags')
    parser.add_argument('p1',
            help='File or directory (all images) to print.  Directory not implemented')

    args = parser.parse_args()
    
    if args.debug:
        import pdb
        pdb.set_trace()

    if args.verbose == 1:
        LOGGING['handlers']['rotate']['level'] = 'INFO'
        LOGGING['handlers']['rotate']['level'] = 'INFO'
        LOGGING['handlers']['console']['level'] = 'INFO'
        LOGGING['handlers']['console']['level'] = 'INFO'
    elif args.verbose > 1:
        LOGGING['handlers']['rotate']['level'] = 'DEBUG'
        LOGGING['handlers']['rotate']['level'] = 'DEBUG'
        LOGGING['handlers']['console']['level'] = 'DEBUG'
        LOGGING['handlers']['console']['level'] = 'DEBUG'
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(__name__)

    try:
        img = Image.open(args.p1)
        exif = {
            TAGS[k]: v
            for k, v in img._getexif().items()
            if k in TAGS
        }
    except Exception as e:
        exif = {'Error' : 'Unable to parse file: {0}'.format(e)}
    print("PIL:")
    print("====")
    if args.all:
        for k, v in exif.items():
            if k in ['SceneType', 'ComponentsConfiguration', 'FileSource', 'MakerNote']:
                continue
            print "{0}: {1}".format(k,v)
    else:
        for k in PIL_TAGS:
            v = exif.get(k, None)
            if v is not None:
                print "{0}: {1}".format(k,v)

    if args.all:
        print("\n\n")
        print("GExiv2:")
        print("=======")

        img = GExiv2.Metadata(sys.argv[1])
        keys = [x for x in img]
        for key in keys:
            print "{0}: {1}".format(key, img[key])
        keywords = img.get_tag_multiple('Iptc.Application2.Keywords')
        print("Keywords: {0}".format(keywords))

    return



if __name__ == "__main__":
    main()

