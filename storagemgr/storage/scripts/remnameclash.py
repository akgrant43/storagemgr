"""
Script: remnameclash.py

Trash files that were accidentally added twice based on there having a name clash.

WARNING: This could unintentionally delete originals where high speed was used and the
timestamp is unchanged between photos.
"""

import re
import pdb

from datetime import datetime
from os import mkdir
from os.path import isdir, exists, join, expanduser
from shutil import move

from django.conf import settings
from logger import init_logging

logger = init_logging(__name__)

# States
STATE_SEARCHING = "Searching"
STATE_HAVE_AVOID = "Have Avoid"

TRASH_DIR = expanduser("~/StorageMgr Trash/")

EXISTING_FN_RE = re.compile(r"(IMG|VID)-(?P<date>[0-9]{8})-(?P<hour>[0-9]{2})(?P<minute>[0-9]{2})(?P<second>[0-9]{2})-(?P<iterator>[0-9]{1,3}).[a-z]{3}")
DUPLICATE_FN_RE = re.compile(r"(?P<media>IMG|VID)-(?P<date>[0-9]{8})-(?P<hour>[0-9]{2})(?P<minute>[0-9]{2})(?P<second>[0-9]{2})-(?P<millisecond>[0-9]{1,3})-(?P<iterator>[0-9]{1,3}).[a-z]{3}")

def get_existing_fn(log_entry):
    "Parse the supplied log entry for the existing file name"
    words = log_entry.strip().split()
    fn = words[-1]
    fnre = EXISTING_FN_RE.search(fn)
    if fnre is None:
        msg = "Failed to find existing fn"
        logger.critical(msg)
        raise Exception(msg)
    return fnre


def get_duplicate_fn(log_entry):
    "Parse the supplied log entry for the existing file name"
    words = log_entry.strip().split()
    fn = words[9]
    fnre = DUPLICATE_FN_RE.search(fn)
    if fnre is None:
        msg = "Failed to find duplicate fn"
        logger.critical(msg)
        raise Exception(msg)
    return fnre


def run(*args):
    pdb.set_trace()
    logger.info("remnameclash starting")
    logfn = args[0]

    if not isdir(TRASH_DIR):
        mkdir(TRASH_DIR)

    logfp = open(logfn, "r")

    state = STATE_SEARCHING
    line_number = 0
    for log_entry in logfp:
        logger.info("P: {0}".format(log_entry).strip())
        line_number += 1
        if "avoiding name clash for" in log_entry:
            if state != STATE_SEARCHING:
                msg = "Found avoiding record while not searching"
                logger.critical(msg)
                raise Exception(msg)
            state = STATE_HAVE_AVOID
            existing_fn = get_existing_fn(log_entry)
            avoiding_line_number = line_number
            logger.info("Found existing fn {0}".format(existing_fn.group()))
        elif "added" in log_entry:
            if state != STATE_HAVE_AVOID:
                msg = "Found added record without avoid record, ignoring"
                logger.info(msg)
                continue
            if line_number > (avoiding_line_number + 3):
                msg = "added line ({0}) too far from avoiding line ({1})".format(line_number, avoiding_line_number)
                logger.critical(msg)
                raise Exception(msg)
            duplicate_fn = get_duplicate_fn(log_entry)
            if duplicate_fn.group('media') == 'IMG':
                dup_dir = settings.IMAGES_ARCHIVE
            elif duplicate_fn.group('media') == 'VID':
                dup_dir = settings.VIDEO_ARCHIVE
            else:
                raise Exception("Unknown media type: {0}".format(duplicate_fn.group('media')))
            existing_date = datetime.strptime(existing_fn.group('date'), '%Y%m%d')
            dup_date = datetime.strptime(duplicate_fn.group('date'), '%Y%m%d')
            if existing_date != dup_date:
                msg = "Duplicate has different date {0} / {1}".format(existing_date, dup_date)
                logger .critical(msg)
                raise Exception(msg)
            if dup_date.year != 2014:
                msg = "Unexpected year: {0}".format(dup_date.year)
                logger.critical(msg)
                raise Exception(msg)
            dup_dir = join(dup_dir, dup_date.strftime("%Y"),
                           dup_date.strftime("%m%b"))
            dup_path = join(dup_dir, duplicate_fn.group())
            if not exists(dup_path):
                msg = "Duplicate path doesn't exist: {0}".format(dup_path)
                logger.critical(msg)
                raise Exception(msg)
            logger.info("Trashing {0}".format(dup_path))
            move(dup_path, TRASH_DIR)
    logger.info("remnameclash finished")