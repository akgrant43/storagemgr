#!/usr/bin/env python
"""Dump EXIF data using PIL and pyexiv2 (just for debugging)"""

import sys
from PIL import Image
from gi.repository import GExiv2
from PIL.ExifTags import TAGS
import pyexiv2

try:
    img = Image.open(sys.argv[1])
    exif = {
        TAGS[k]: v
        for k, v in img._getexif().items()
        if k in TAGS
    }
except Exception as e:
    exif = {'Error' : 'Unable to parse file: {0}'.format(e)}
print("PIL:")
print("====")
for k, v in exif.items():
    if k in ['SceneType', 'ComponentsConfiguration', 'FileSource', 'MakerNote']:
        continue
    print "{0}: {1}".format(k,v)

print("\n\n")
print("PyExiv2:")
print("========")

img = pyexiv2.metadata.ImageMetadata(sys.argv[1])
img.read()
for k,v in img.items():
    #print "{0}: {1}".format(k,v)
    print(v)


print("\n\n")
print("GExiv2:")
print("=======")

img = GExiv2.Metadata(sys.argv[1])
keys = [x for x in img]
for key in keys:
    print "{0}: {1}".format(key, img[key])
keywords = img.get_tag_multiple('Iptc.Application2.Keywords')
print("Keywords: {0}".format(keywords))
