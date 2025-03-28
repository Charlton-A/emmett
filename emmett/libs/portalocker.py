#!/usr/bin/env python
# -*- coding: utf-8 -*-
# portalocker.py
# Cross-platform (posix/nt) API for flock-style file locking.
#                  Requires python 1.5.2 or better.

"""
Cross-platform (posix/nt) API for flock-style file locking.

Synopsis:

   import portalocker
   file = open(\"somefile\", \"r+\")
   portalocker.lock(file, portalocker.LOCK_EX)
   file.seek(12)
   file.write(\"foo\")
   file.close()

If you know what you're doing, you may choose to

   portalocker.unlock(file)

before closing the file, but why?

Methods:

   lock( file, flags )
   unlock( file )

Constants:

   LOCK_EX
   LOCK_SH
   LOCK_NB

I learned the win32 technique for locking files from sample code
provided by John Nielsen <nielsenjf@my-deja.com> in the documentation
that accompanies the win32 modules.

Author: Jonathan Feinberg <jdf@pobox.com>
Version: $Id: portalocker.py,v 1.3 2001/05/29 18:47:55 Administrator Exp $
"""

os_locking = None
try:
    os_locking = "gae"
except Exception:
    try:
        import fcntl

        os_locking = "posix"
    except Exception:
        try:
            import pywintypes
            import win32con
            import win32file

            os_locking = "windows"
        except Exception:
            pass

if os_locking == "windows":
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # the default
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY

    # is there any reason not to reuse the following structure?

    __overlapped = pywintypes.OVERLAPPED()

    def lock(file, flags):
        hfile = win32file._get_osfhandle(file.fileno())
        win32file.LockFileEx(hfile, flags, 0, 0x7FFF0000, __overlapped)

    def unlock(file):
        hfile = win32file._get_osfhandle(file.fileno())
        win32file.UnlockFileEx(hfile, 0, 0x7FFF0000, __overlapped)


elif os_locking == "posix":
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB

    def lock(file, flags):
        fcntl.flock(file.fileno(), flags)

    def unlock(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


else:
    # if platform.system() == 'Windows':
    #    logger.error('no file locking, you must install the win32 extensions from: http://sourceforge.net/projects/pywin32/files/')
    # elif os_locking != 'gae':
    #    logger.debug('no file locking, this will cause problems')

    LOCK_EX = None
    LOCK_SH = None
    LOCK_NB = None

    def lock(file, flags):
        pass

    def unlock(file):
        pass


class LockedFile(object):
    def __init__(self, filename, mode="rb"):
        self.filename = filename
        self.mode = mode
        self.file = None
        if "r" in mode:
            kwargs = {"encoding": "utf8"} if "b" not in mode else {}
            self.file = open(filename, mode, **kwargs)
            lock(self.file, LOCK_SH)
        elif "w" in mode or "a" in mode:
            self.file = open(filename, mode.replace("w", "a"))
            lock(self.file, LOCK_EX)
            if "a" not in mode:
                self.file.seek(0)
                self.file.truncate()
        else:
            raise RuntimeError("invalid LockedFile(...,mode)")

    def read(self, size=None):
        return self.file.read() if size is None else self.file.read(size)

    def readline(self):
        return self.file.readline()

    def readlines(self):
        return self.file.readlines()

    def write(self, data):
        self.file.write(data)
        self.file.flush()

    def close(self):
        if self.file is not None:
            unlock(self.file)
            self.file.close()
            self.file = None

    def __del__(self):
        if self.file is not None:
            self.close()


def read_locked(filename):
    fp = LockedFile(filename, "r")
    data = fp.read()
    fp.close()
    return data


def write_locked(filename, data):
    fp = LockedFile(filename, "wb")
    data = fp.write(data)
    fp.close()
