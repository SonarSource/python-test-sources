"""Filename globbing utility."""

import os
import re
import fnmatch

from typing import List, Iterator, Iterable, Any, AnyStr

__all__ = ["glob", "iglob"]

def glob(pathname: AnyStr) -> List[AnyStr]:
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    return list(iglob(pathname))

def iglob(pathname: AnyStr) -> Iterator[AnyStr]:
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    if not has_magic(pathname):
        if os.path.lexists(pathname):
            yield pathname
        return
    dirname, basename = os.path.split(pathname)
    if not dirname:
        for name in glob1(None, basename):
            yield name
        return
    if has_magic(dirname):
        dirs = iglob(dirname) # type: Iterable[AnyStr]
    else:
        dirs = [dirname]
    if has_magic(basename):
        glob_in_dir = glob1 # type: Any
    else:
        glob_in_dir = glob0
    for dirname in dirs:
        for name in glob_in_dir(dirname, basename):
            yield os.path.join(dirname, name)

# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames. `glob1` accepts a pattern while `glob0`
# takes a literal basename (so it only has to check for its existence).

def glob1(dirname: AnyStr, pattern: AnyStr) -> List[AnyStr]:
    if not dirname:
        if isinstance(pattern, bytes):
            dirname = bytes(os.curdir, 'ASCII')
        else:
            dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except os.error:
        return []
    if pattern[0] != '.':
        names = [x for x in names if x[0] != '.']
    return fnmatch.filter(names, pattern)

def glob0(dirname: AnyStr, basename: AnyStr) -> List[AnyStr]:
    if basename == '':
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        if os.path.isdir(dirname):
            return [basename]
    else:
        if os.path.lexists(os.path.join(dirname, basename)):
            return [basename]
    return []


magic_check = re.compile('[*?[]')
magic_check_bytes = re.compile(b'[*?[]')

def has_magic(s: AnyStr) -> bool:
    if isinstance(s, bytes):
        match = magic_check_bytes.search(s)
    else:
        match = magic_check.search(s)
    return match is not None
