import argparse
import os
import sys
from . import copyf
import stat

WIDTH = 119 # this should be *less* (not equal) than the width
            # of your console window (79 default)

ignore = [
    'System Volume Information',
    'RECYCLER',
    '$RECYCLE.BIN',
    '$VAULT$.AVG',
]

test = False


def ctime(f, ctime_ns):
    # on windows, set ctime (creation time) for files & folders.
    # https://stackoverflow.com/q/4996405
    # https://stackoverflow.com/q/4998814
    try:
        from ctypes import windll, wintypes, byref
        import msvcrt
    except ImportError:
        return
    # See: https://support.microsoft.com/en-us/help/167296
    timestamp = int((ctime_ns / 100) + 116444736000000000)
    ctime = wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)
    if os.path.isdir(f):
        handle = windll.kernel32.CreateFileW(f, 256, 0, None, 3, 128 | 0x02000000, None)
    else:
        handle = windll.kernel32.CreateFileW(f, 256, 0, None, 3, 128, None)
    windll.kernel32.SetFileTime(handle, byref(ctime), None, None)
    windll.kernel32.CloseHandle(handle)


def sync(filepath, src, dst):
    new = None
    newtime = -2
    for i in src:
        f = os.path.join(i, filepath)
        if os.path.isfile(f):
            if os.path.getmtime(f) > newtime:
                new = f
                newtime = os.path.getmtime(f)

    if not new:
        error('Error copying file - could not find a source path:\n\t%s' % (filepath))
        for i in src:
            f = os.path.join(i, filepath)
            print((os.path.isfile(f), os.path.getmtime(f), newtime))
        return

    if newtime == -2:
        error('mtime is wrong:\n\t%s' % filepath)
        return

    for i in dst:
        copy_data = True
        f = os.path.join(i, filepath)
        if os.path.isfile(f):
            if os.path.getsize(f) == os.path.getsize(new):
                if os.path.getmtime(f) > newtime - 10:
                    copy_data = False
                    continue

        write('Copying file %s -> %s' % (new, i))
        try:
            if test: continue
            try:
                if copy_data:
                    copyf.copyfile(new, f)
            except:
                if os.path.exists(f):
                    os.remove(f)
                raise
            # shutil.copystat(new, f) # We dont want to copy permissions!
            # (or do we?)
            st = os.stat(new)
            mode = stat.S_IMODE(st.st_mode)
            os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))
            os.chmod(f, mode)
            ctime(f, st.st_ctime_ns)

        except IOError as e:
            error('Could not copy file %s:\n\t%s' % (new, e))


def walk(src, dst):
    done = {}
    write('Syncing directories..')
    write('Sources: {}'.format(', '.join(src)))
    write('Destinations: {}'.format(', '.join(dst)))

    after_ctimes = []
    for dir in src:
        for path, dirs, files in os.walk(dir):
            files.sort()
            dirs.sort()
            for i in ignore:
                if i in dirs:
                    dirs.remove(i)
                    write('Ignoring %s' % i)
            st = os.stat(os.path.join(dir, path))
            try:
                write('Scanning path %s...' % path, False)
                assert path.startswith(dir)
                path = path[len(dir):]
                for i in dst:
                    d = os.path.join(i, path)
                    if not os.path.isdir(d):
                        write('Creating dir %s' % d)
                        if test: continue
                        os.mkdir(d)
                        # ctime will come from first src
                        ctime(d, st.st_ctime_ns)
                    os.utime(d, ns=(st.st_atime_ns, st.st_mtime_ns))
                    after_ctimes.append((d, (st.st_atime_ns, st.st_mtime_ns)))
                for i in files:
                    f = os.path.join(path, i)
                    sync(f, src, dst)
            except (IOError, WindowsError) as e:
                error('Could not sync directory %s:\n\t%s' % (path, e))

    for d, nss in reversed(after_ctimes):
        write('Setting times for dir %s...' % d)
        os.utime(d, ns=nss)

    write('Directories synced.')


errors = []
def error(s):
    import traceback
    traceback.print_exc()
    write(s)
    errors.append(s)


def write(s, p=True):
    s = s.encode('ascii', 'replace').decode('ascii')
    sys.stdout.write('\b'*WIDTH + s[:WIDTH] + ' '*(WIDTH-len(s)) + (p and '\r\n' or ''))
    sys.stdout.flush()


def main(options):
    src = []
    dst = []
    # dirs should be in the form r'K:\SCHOOL\CPSC233\' (trailing slashes)
    # ^ why?
    print()
    for i in options:

        if i[0] == '-':
            if i == '-t':
                global test
                test = True

            continue

        t, i = i.split('=',1)
        d = os.path.normcase(os.path.normpath(i))+'\\'
        if t == 's':
            if not os.path.isdir(d):
                print('%s is not a directory!' % d)
                continue
                raise SystemExit
            src.append(d)
        if t == 'd':
            dst.append(d)
        if t == 'i':
            ignore.append(d[:-1])

    walk(src, dst)

    if test:
        print()
        print('Test mode -- No files were acctually copied')

    if errors:
        print()
        print('The following errors occured:')
        for i in errors:
            print()
            print(i)


