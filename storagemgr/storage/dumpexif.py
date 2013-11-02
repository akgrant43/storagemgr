#!/usr/bin/env python
"""Dump EXIF data using PIL and pyexiv2 (just for debugging)"""

import sys
import Image
from PIL.ExifTags import TAGS
import pyexiv2

img = Image.open(sys.argv[1])
exif = {
    TAGS[k]: v
    for k, v in img._getexif().items()
    if k in TAGS
}
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
