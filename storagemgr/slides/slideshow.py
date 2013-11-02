#!/usr/bin/env python
"""Slideshow displays the supplied list of files.

Originally based on: https://gist.github.com/zed/8b05c3ea0302f0e2c14c/ (thanks to zed on github)

Changes include:

* Use black background
* Use full screen by default
* Handle EXIF Orientation data
* Only run through images once (default)
* Up and Down keys lengthen and shorten the display time
"""
import logging
import os
import platform
import sys
from collections import deque
from itertools import cycle

import Tkinter as tk
import Image
import ImageTk
from Image import FLIP_LEFT_RIGHT, FLIP_TOP_BOTTOM, ROTATE_90, ROTATE_180, ROTATE_270

#psutil = None  # avoid "redefinition of unused 'psutil'" warning
#try:
    #import psutil
#except ImportError:
    #pass

debug = logging.debug

ORIENTATIONS = [
    None,                           # 0 never used
    [],                             # 1 no action required
    [FLIP_LEFT_RIGHT],              # 2
    [ROTATE_180],                   # 3
    [FLIP_TOP_BOTTOM],              # 4
    [ROTATE_270, FLIP_LEFT_RIGHT],  # 5
    [ROTATE_270],                   # 6
    [ROTATE_90, FLIP_LEFT_RIGHT],   # 7
    [ROTATE_90]                     # 8
]

class Slideshow(object):
    def __init__(self, parent, filenames, slideshow_delay=2, history_size=100):
        self._parent = parent
        self.ma = parent.winfo_toplevel()
        self.filenames = filenames
        self._photo_image = None  # must hold reference to PhotoImage
        self._id = None  # used to cancel pending show_image() callbacks
        self.imglbl = tk.Label(parent)  # it contains current image
        # label occupies all available space
        self._delay = slideshow_delay * 1000
        self._idx = 0 # index of the current slide
        self.imglbl.pack(fill=tk.BOTH, expand=True)
        self.show_slides()
        return

    def show_slides(self, event_unused=None):
        # start slideshow after settling in period
        self._id = self.imglbl.after(self._delay, self._slideshow)

    def _slideshow(self):
        self.show_image()
        self._idx += 1
        if self._idx < len(self.filenames):
            self._id = self.imglbl.after(self._delay, self._slideshow)

        else:
            self.imglbl.after(self._delay * 2, self.quit)
        return

    def show_image(self):
        filename = self.filenames[self._idx]
        debug("load %r", filename)
        image = Image.open(filename)  # note: let OS manage file cache
        exif = image._getexif()
        # Orientation is 274
        orientation = exif.get(274, 1)
        # See:
        # - http://www.daveperrett.com/articles/2012/07/28/exif-orientation-handling-is-a-ghetto/
        # - http://omz-software.com/pythonista/docs/ios/Image.html
        if orientation >= 2 and orientation <= 8:
            for action in ORIENTATIONS[orientation]:
                image = image.transpose(action)

        # shrink image inplace to fit in the application window
        w, h = self.ma.winfo_width(), self.ma.winfo_height()
        if image.size[0] > w or image.size[1] > h:
            # note: ImageOps.fit() copies image
            # preserve aspect ratio
            image.thumbnail((w - 2, h - 2), Image.ANTIALIAS)
            debug("resized: win %s >= img %s", (w, h), image.size)

        # note: pasting into an RGBA image that is displayed might be slow
        # create new image instead
        self._photo_image = ImageTk.PhotoImage(image)
        self.imglbl.configure(background='black', image=self._photo_image)

        # set application window title
        self.ma.wm_title(filename)

    def quit(self, event_unused=None):
        self._parent.destroy()

    def _show_image_on_next_tick(self, cancel=True):
        # cancel previous callback schedule a new one
        if self._id is not None and cancel:
            self.imglbl.after_cancel(self._id)
        self._id = self.imglbl.after(100, self.show_image)

    def next_image(self, event_unused=None):
        if self._idx >= len(self.filenames):
            return
        self._idx += 1
        self._show_image_on_next_tick()

    def prev_image(self, event_unused=None):
        if self._idx == 0:
            return
        self._idx -= 1
        self._show_image_on_next_tick()

    def inc_delay(self, event_unused=None):
        self._delay += 200
        debug("delay: {0}".format(self._delay))

    def dec_delay(self, event_unused=None):
        self._delay -= 200
        if self._delay < 1:
            self._delay = 1
        debug("delay: {0}".format(self._delay))

    def fit_image(self, event=None, _last=[None] * 2):
        """Fit image inside application window on resize."""
        if event is not None and event.widget is self.ma and (
            _last[0] != event.width or _last[1] != event.height):
            # size changed; update image
            _last[:] = event.width, event.height
            self._show_image_on_next_tick(cancel=False)

    @classmethod
    def fullscreen(cls, files, delay=2):
        root = tk.Tk()
        root.attributes('-fullscreen', True)

#         if logging.getLogger().isEnabledFor(logging.DEBUG) and psutil is not None:
#             def report_usage(prev_meminfo=None, p=psutil.Process(os.getpid())):
#                 # find max memory
#                 if p.is_running():
#                     meminfo = p.get_memory_info()
#                     if meminfo != prev_meminfo and (
#                         prev_meminfo is None or meminfo.rss > prev_meminfo.rss):
#                         prev_meminfo = meminfo
#                         debug(meminfo)
#                     root.after(500, report_usage, prev_meminfo)  # report in 0.5s
#             report_usage()

        try:  # start slideshow
            app = cls(root, files, delay)
        except StopIteration:
            sys.exit("no image files found in %r" % (imagedir,))
    
        # configure keybindings
        root.bind("<Escape>", lambda _: root.destroy())  # exit on Esc
        root.bind('<Prior>', app.prev_image)
        root.bind('<Up>',    app.inc_delay)
        root.bind('<Left>',  app.prev_image)
        root.bind('<Next>',  app.next_image)
        root.bind('<Down>',  app.dec_delay)
        root.bind('<Right>', app.next_image)
        root.bind('<Return>', app.show_slides)
    
        root.bind("<Configure>", app.fit_image)  # fit image on resize
        root.focus_set()
        root.mainloop()
        
        

def get_image_files(rootdir):
    for path, dirs, files in os.walk(rootdir):
        dirs.sort()   # traverse directory in sorted order (by name)
        files.sort()  # show images in sorted order
        for filename in files:
            if filename.lower().endswith('.jpg'):
                yield os.path.join(path, filename)


def main():
    logging.basicConfig(format="%(asctime)-15s %(message)s", datefmt="%F %T",
                        level=logging.DEBUG)

    # get image filenames
    imagedir = sys.argv[1] if len(sys.argv) > 1 else '.'
    image_filenames = get_image_files(imagedir)

    Slideshow.fullscreen(image_filenames)
    return

if __name__ == '__main__':
    main()
