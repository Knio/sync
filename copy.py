"""Utility functions for copying files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.

"""

import os
import sys
import stat
from os.path import abspath
import fnmatch


class Error(EnvironmentError):
    pass

try:
    WindowsError
except NameError:
    WindowsError = None

import threading
import time

def hsize(x):
    n = ['B','kB', 'MB', 'GB', 'TB']
    i = 0
    x = float(x)
    while x >= 1024:
        x /= 1024
        i += 1
        
    return '%*.2f %s' % (7, x, n[i])


def threadcopy(fsrc, fdst, length=1*1024*1024, buffer=32):
    
    data = []
    done = [False, False]
    
    
    def read():
        
        while not done[1]:
            buf = fsrc.read(length)
            if not buf: break # eof
            data.append(buf)
            
            while len(data) > buffer and not done[1]: time.sleep(0.1)
            
        if done[1]:
            raise Exception('An error occurred while copying the file (1)')
        
        done[0] = True
        
        
    thread = threading.Thread(target=read)
    thread.start()
    
    try:
        assert thread.isAlive() or data
        
        total = 0
        
        while (data or thread.isAlive()): # TODO: more condition (is thread really ok?)
            while not data: time.sleep(0.1)
            buf = data.pop(0)
            fdst.write(buf)
            
            
            # statistics
            total += len(buf);
            buffr = sum(map(len,data))
            
            sys.stdout.write('\b'*100)
            sys.stdout.write('Copied: %-20s   Buffered: %-20s' % (hsize(total), hsize(buffr)))
        
        if not done[0]:
            raise Exception('An error occurred while copying the file (2)')
    
    finally:
        done[1] = True     # signal the read thread to stop
        


def copyfileobj(fsrc, fdst, length=16*1024*1024):
    """copy data from file-like object fsrc to file-like object fdst"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

def _samefile(src, dst):
    # Macintosh, Unix.
    if hasattr(os.path,'samefile'):
        try:
            return os.path.samefile(src, dst)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    return (os.path.normcase(os.path.abspath(src)) ==
            os.path.normcase(os.path.abspath(dst)))

def copyfile(src, dst, copyfnc=copyfileobj, *fargs, **dargs):
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error, "`%s` and `%s` are the same file" % (src, dst)
    
    fsrc = None
    fdst = None
    try:
        assert os.path.isfile(src)
        
        sz = os.path.getsize(src)
        
        fsrc = open(src, 'rb')
        fdst = open(dst, 'wb')
        
        # try to allocate the whole file size to reduce fragmentation
        
        
        # this works on windows! :D
        fdst.truncate(sz)
        
        # This might be needed on other systems. 
        
        #fdst.seek(sz-1)
        #fdst.write('\0')
        #fdst.seek(0)
        
        copyfnc(fsrc, fdst, *fargs, **dargs)
        
        assert fdst.tell() == sz
        
        
        
    finally:
        if fdst:
            fdst.truncate() # sync will think it worked if the file sizes match
            fdst.close()
        if fsrc:
            fsrc.close()

def copymode(src, dst):
    """Copy mode bits from src to dst"""
    if hasattr(os, 'chmod'):
        st = os.stat(src)
        mode = stat.S_IMODE(st.st_mode)
        os.chmod(dst, mode)

def copystat(src, dst):
    """Copy all stat info (mode bits, atime, mtime, flags) from src to dst"""
    st = os.stat(src)
    mode = stat.S_IMODE(st.st_mode)
    if hasattr(os, 'utime'):
        os.utime(dst, (st.st_atime, st.st_mtime))
    if hasattr(os, 'chmod'):
        os.chmod(dst, mode)
    if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
        os.chflags(dst, st.st_flags)


def copy(src, dst, func=threadcopy, *fargs, **dargs):
    """Copy data and mode bits ("cp src dst").
    The destination may be a directory.
    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst, func, *fargs, **dargs)
    copymode(src, dst)


    
def main():
    if not len(sys.argv) == 3:
        print "Takes exactly 2 args"
        return
    
    
    
    copy(sys.argv[1], sys.argv[2], threadcopy)
    
if __name__ == '__main__':
    main()

