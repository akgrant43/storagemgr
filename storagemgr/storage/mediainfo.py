"""
Module: mediainfo.py

Provide video metadata by calling mediainfo
"""

import pytz
import re
from collections import defaultdict
from dateutil import parser as date_parser
from datetime import datetime
from subprocess import Popen, PIPE

from logger import init_logging
logger = init_logging(__name__)

DATE_RE1 = re.compile(r'(?P<tz>[A-Z]{3}) (?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2}) (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})')
DATE_RE2 = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\+([0-9]{4})')

class MediaInfo(object):
    def __init__(self, file_name):
        self.file_name = file_name

        # Retrieve and parse the metadata
        proc = Popen(['mediainfo', file_name], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            msg = "mediainfo exited with status: {0}".format(proc.returncode)
            logger.error(msg)
            raise OSError(msg)
        if len(err) > 0:
            msg = "mediainfo exited with error message: {0}".format(err)
            logger.error(msg)
            raise OSError(msg)
        self.by_category = defaultdict(lambda : defaultdict(list))
        self.metadata = defaultdict(list)
        category = 'Default'
        for line in out.splitlines():
            if ':' in line:
                fields = line.split(':')
                key = fields[0].strip()
                value = ':'.join(fields[1:]).strip()
                self.by_category[category][key].append(value)
                self.metadata[key].append(value)
            else:
                category = line.strip()
        return

    def get(self, field_name, category=None, default=None):
        if category is None:
            result = self.metadata.get(field_name, default)
        else:
            result = self.by_category[category].get(field_name, default)
        return result

    def filter(self, regex, default=None):
        "Answer a dictionary of keys matching regex"
        result = {}
        keys = self.metadata.keys()
        re1 = re.compile(regex)
        for key in keys:
            if re1.search(key):
                result[key] = self.metadata[key]
        return result

    def filter_values(self, regex):
        "Answer a flat list of values for keys matching regex"
        result = []
        keys = self.metadata.keys()
        re1 = re.compile(regex)
        for key in keys:
            if re1.search(key):
                for v in self.metadata[key]:
                    result.append(v)
        return result

    def print_dict(self):
        for k1, v1 in self.by_category.iteritems():
            print("{k}:".format(k=k1))
            print("=" * (len(k1)+1))
            for k2, v2 in v1.iteritems():
                print("    {k}: {v}".format(k=k2, v=v2))

    def to_datetime(self, dt_string):
        "Convenience routine to convert a string in mediainfo format to a datetime"
        dtre = DATE_RE1.match(dt_string)
        if dtre is not None:
            tzs = dtre.group('tz')
            tz = pytz.timezone(tzs)
            year = dtre.group('year')
            month = dtre.group('month')
            day = dtre.group('day')
            hour = dtre.group('hour')
            minute = dtre.group('minute')
            second = dtre.group('second')
            dt = datetime(int(year), int(month), int(day),
                int(hour), int(minute), int(second))
            dt = tz.localize(dt)
        elif DATE_RE2.match(dt_string) is not None:
            dt = date_parser.parse(dt_string)
        else:
            import pdb; pdb.set_trace()
            msg = "Unrecognised dt_string: {0}".format(dt_string)
            raise ValueError(msg)
        return dt

    def earliest_date(self):
        "Answer the earliest date in the receivers file"
        dts = self.filter_values('date')
        if len(dts) == 0:
            return None
        dts = set(dts)
        dts = [self.to_datetime(x) for x in dts]
        dts.sort()
        # Filter out default date of 1904-01-01 00:00:00
        dt = None
	l = len(dts)-1
        for i in range(l,-1,-1):
            if dts[i].year > 1904:
                dt = dts[i]
        return dt


if __name__ == "__main__":
    # Dev testing
    import sys

    fn = sys.argv[1]
    mi = MediaInfo(fn)
    mi.print_dict()
    import pdb; pdb.set_trace()
    dt = mi.earliest_date()
    pass

