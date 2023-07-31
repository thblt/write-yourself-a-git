#!/usr/bin/env python3

import argparse
import sys
from collections import defaultdict
from os import listdir, walk as fs_walk, path, stat
from os.path import abspath, isdir, relpath
from pathlib import Path
from shutil import copyfile

# We're going to be working with a ton of triples, these are indices.
BASE = 0
LEFT = 1
RIGHT = 2

IDENTICAL=True
DIFFERENT=False

diff_cache = dict()

def merge(conf):
    paths = list_paths(conf)
    conflicts = list()
    for (path, presence) in paths.items():
        if not rule_creation(conf, path, presence) \
            or rule_deletion(conf, path, presence) \
            or rules_ident_modif_merg(conf, path, presence):
            conflicts.append(path)

    return conflicts


def rule_identity(conf, path, versions):
    bpath = base_path(conf, path)
    holds = versions == [True,True,True] \
        and diff_files (bpath, left_path(conf, path)) \
        and diff_files (bpath, right_path(conf, path))

    if holds:
        trace(f"Identity holds for {path}")
        copyfile(bpath, out_path(conf, path))

    return holds

def base_path(conf, path):
    return path_join(conf.base, path)

def left_path(conf, path):
    return path_join(conf.left, path)

def right_path(conf, path):
    return path_join(conf.right, path)

def rule_creation(conf, path, presence):
    created_left = presence == [False,True,False]
    created_right = presence == [False,False,True]

    if created_left:
        conf.trace(f"Creation (left) holds for {path}")
        copyfile(left_path(conf,path), out_path(conf, path))
        return True
    elif created_right:
        conf.trace(f"Creation (right) holds for {path}")
        copyfile(right_path(conf,path), out_path(conf, path))
        return True
    else:
        return False

def rule_deletion(conf, path, presence):
    deleted_left = presence == [True,False,True]
    deleted_right = presence == [True,True,False]

    bpath = base_path(conf, path)

    if deleted_left \
       and diff_files(bpath, path_right(conf, path)):
        conf.trace(f"Deletion (left) holds for {path}")
        return True
    elif deleted_right \
       and diff_files(bpath, path_left(conf, path)):
        conf.trace(f"Deletion (right) holds for {path}")
        return True
    else:
        return False

def rules_ident_modif_merge(conf, path, presence):
    bpath = base_path(conf, path)

    if presence != [True,True,True]:
        return False

    modified_left = diff_files (bpath, left_path(conf, path))
    modified_right = diff_files (bpath, right_path(conf, path))

    if not (modified_left or modified_right):
        conf.trace(f"Identity holds for {path}")
        copyfile(base_path(conf, path), out_path(conf, path))
        return True
    elif modified_left and not modified_right:
        conf.trace(f"Modif (left) holds for {path}")
        copyfile(left_path(conf, path), out_path(conf, path))
        return True
    elif modified_right and not modified_left:
        conf.trace(f"Modif (right) holds for {path}")
        copyfile(right_path(conf, path), out_path(conf, path))
        return True
    else:
        conf.trace(f"Merge holds for {path}")
        return merge_files(conf, path)

def rule_modification(conf, path, presence):
    if presence != [True,True,True]:
        return False

    bpath = base_path(conf, path)
    modified_left = diff_files(bpath, )

def list_paths(root):
    ret = list()

    for dir, _, files in fs_walk(root):
        for file in files:
            file = relpath(path.join(dir, file), root)
            ret.append(file)
    return ret

def diff_files(conf, a, b):
    global diff_cache

    a = abspath(a)
    b = abspath(b)

    conf.trace(f"diff_files: Diffing {a} and {b}")

    if a < b:
        index = (a,b)
    else:
        index = (b,a)

    if index in diff_cache:
        conf.trace("  Using cached comparison")
        return diff_cache[index]

    stat_a = stat(a)
    stat_b = stat(b)

    if stat_a.st_size != stat_b.st_size:
        diff_cache[index] = DIFFERENT
        return DIFFERENT

    conf.trace("  Using deep compare")
    with open(a, "rb") as fd_a:
        with open(b, "rb") as fd_b:
            diff = fd_a.read() == fd_b.read()
            diff_cache[index] = diff
            return diff

def diff_paths(conf):
    base = list_paths(conf.base)
    left = list_paths(conf.left)
    right = list_paths(conf.right)

    ret = defaultdict(lambda: [False,False,False])

    for path in base:
        ret[path][BASE] = True

    for path in left:
        ret[path][LEFT] = True

    for path in right:
        ret[path][right] = True

    return ret

def usage(exitcode=0):
    print("Usage:")
    print("  {} BASE LEFT RIGHT OUTPUT".format(sys.argv[0]))
    exit(exitcode)

def dir_validate(path, check_empty=False):
    if not isdir(path):
        print("Fatal: Not a directory: {}".format(path))
        exit(1)

    if check_empty and listdir(path):
        print("Fatal: Not empty: {}".format(path))
        exit(2)

    return abspath(path)

class Config(object):
    def __init__(self, base, left, right, out, verbose):
        self.base = base
        self.left = left
        self.right = right
        self.out = out
        self.verbose = verbose

    def trace(self, msg):
        if self.verbose:
            print(msg)

def main():
    parser = argparse.ArgumentParser(description="Three-way merge for wyag.")
    parser.add_argument("base", help="Base directory.", type=Path)
    parser.add_argument("left", help="Left directory.", type=Path)
    parser.add_argument("right", help="Right directory.", type=Path)
    parser.add_argument("out", help="Output directory (must be empty).", type=Path)
    parser.add_argument("-v", "--verbose", dest="verbose", help="Talk a lot.")
    args = parser.parse_args(sys.argv[1:])

    conf = Config(
        dir_validate(args.base),
        dir_validate(args.left),
        dir_validate(args.right),
        dir_validate(args.out, check_empty=True),
        args.verbose)

    merge(conf)


if __name__=="__main__":
    main()
