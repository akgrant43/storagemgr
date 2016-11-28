import hashlib
from PIL import Image

from logger import init_logging
logger = init_logging(__name__)

def smhash(fn):
    """Try and return the hash of just the image data.
    If not, the entire file."""

    try:
        img = Image.open(fn)
        img_data = img.tobytes()
        hasher = hashlib.sha256()
        hasher.update(img_data)
        digest = hasher.hexdigest()
        logger.debug("Successfully used image digest: {0} -> {1}".format(
            fn, digest))
    except IOError:
        digest = None
    if digest is None:
        hasher = hashlib.sha256()
        read_size = hasher.block_size * 1024
        with open(fn, 'rb') as fp:
            while True:
                buf = fp.read(read_size)
                if len(buf) == 0:
                    break  
                hasher.update(buf)
        digest = hasher.hexdigest()
        logger.debug("Fallback file digest: {0} -> {1}".format(fn, digest))
    return digest

