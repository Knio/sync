import sys

from . import main

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Sync2 - sync directories')
        print()
        print('usage:')
        print('sync2.py [-t] s=dir1 s=dir2 d=dir3 d=dir4 i=dir5')
        print()
        print('options:')
        print('-t           test run - don\'t acctually copy files')
        print('s=dir        use dir as source')
        print('d=dir        use dir as desination')
        print('i=dir        ignore directories with name dir')
        print()

    main(sys.argv[1:])
