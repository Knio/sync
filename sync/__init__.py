import os
import sys
from . import copyf
import stat

WIDTH = 119 # this should be *less* (not equal) than the width
            # of your console window (79 default)

ignore  = [
    'System Volume Information',
    'RECYCLER',
    '$RECYCLE.BIN',
    '$VAULT$.AVG'
    ]

test    = False


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
        f = os.path.join(i, filepath)
        if os.path.isfile(f):
            if os.path.getsize(f) == os.path.getsize(new):
                if os.path.getmtime(f) > newtime - 10:
                    continue

        write('Copying file %s -> %s' % (new, i))
        try:
            if test: continue
            try:
                copyf.copyfile(new, f)
            except:
                if os.path.exists(f):
                    os.remove(f)
                raise
            # shutil.copystat(new, f) # We dont want to copy permissions!
            # (or do we?)
            st = os.stat(new)
            mode = stat.S_IMODE(st.st_mode)
            os.utime(f, (st.st_atime, st.st_mtime))
            os.chmod(f, mode)

        except IOError as e:
            error('Could not copy file %s:\n\t%s' % (new, e))


def walk(src, dst):
    done = {}
    write('Syncing directories..')

    for dir in src:
        for path, dirs, files in os.walk(dir):
            files.sort()
            dirs.sort(reverse=True)
            for i in ignore:
                if i in dirs:
                    dirs.remove(i)
                    write('Ignoring %s' % i)
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
                for i in files:
                    f = os.path.join(path, i)
                    sync(f, src, dst)
            except (IOError, WindowsError) as e:
                error('Could not sync directory %s:\n\t%s' % (path, e))
    write('Directories synced.')


errors = []
def error(s):
    import traceback
    traceback.print_exc()
    write(s)
    errors.append(s)


def write(s, p=True):
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


