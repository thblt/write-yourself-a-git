import abc          # Abstract (pure virtual) base class
import argparse     # Command-line argument parser
import configparser # Ini-like configuration file reader and writer
import zlib         # Compression library
from hashlib import sha1
import os           # Operating system abstraction (for filesystem access)
import re           # Regular expressions library
import sys          # System functions

argparser = argparse.ArgumentParser()
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")

def main(argv=sys.argv[1:]):
  args = argparser.parse_args(argv)

  globals()["cmd_" + args.command.replace("-", "_")](args)

argsubparsers.add_parser("hello", help="Say hello.")

def cmd_hello(args):
    print("Hello Git, I'm Wyag!")

class Repository(object):
    """A git repository"""

    worktree = None
    gitdir = None

    def __init__(self, path, create=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if create:
            self._create(path)

        if not (os.path.exists(self.gitdir) and os.path.isdir(self.gitdir)):
            raise Exception("Not a Git repository %s" % path)

    def mkpath(self, *components):
        return os.path.join(self.gitdir, *components)

    def _create(self, path):
        """Create a new repository at path."""

        # First, we make sure the path either doesn't exist or is an
        # empty dir.

        if os.path.exists(path):
            if not os.path.isdir(path):
                raise Exception ("%s is not a directory!" % path)
            if os.listdir(path):
                raise Exception("%s is not empty!" % path)
        else:
            os.makedirs(path)

        os.makedirs(self.mkpath("."))
        os.mkdir(self.mkpath("branches"))
        os.mkdir(self.mkpath("objects"))
        os.mkdir(self.mkpath("objects/info"))
        os.mkdir(self.mkpath("objects/pack"))
        os.mkdir(self.mkpath("hooks"))
        os.mkdir(self.mkpath("info"))
        os.mkdir(self.mkpath("refs"))
        os.mkdir(self.mkpath("refs/tags"))
        os.mkdir(self.mkpath("refs/heads"))

        # .git/description
        with open(self.mkpath("description"), "w") as f:
            f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

        # .git/HEAD
        with open(self.mkpath("HEAD"), "w") as f:
            f.write("ref: refs/heads/master\n")

        with open(self.mkpath("config"), "w") as f:
            config = configparser.ConfigParser()
            config.add_section("core")
            config.set("core", "\trepositoryformatversion", "0")
            config.set("core", "\tfilemode", "true")
            config.set("core", "\tbare", "false")
            config.set("core", "\tlogallrefupdates", "true")

            config.write(f)

            return Repository(path)

argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository.")

def cmd_init(args):
    Repository(args.path, True)

class GitObject (abc.ABC):
    """ A generic Git object. """

    repo = None
    id = None

    def __init__(repo, id=None, data=None):
        self.repo=repo
        self.id=id

        if data:
            self.deserialize(data)

    @abc.abstractmethod
    def deserialize(self):
        pass

    @abc.abstractmethod
    def serialize(self):
        pass

class GitBlob(GitObject): pass
class GitCommit(GitObject): pass
class GitTag(GitObject): pass
class GitTree(GitObject): pass

def read_object(repo, hash):
    """Read object hash from git repository repo.  This returns a GitObject
    whose exact type depends on the object."""
    path = repo.mkpath("objects", hash[0:2], hash[2:])

    with open (path, "rb") as f:
        raw = zlib.decompress(f.read())

        # Read object type
        x = raw.find(b' ')
        fmt = raw[0:x]

        # Pick matching constructor
        try:
            constructor = {
                b'commit' : GitCommit,
                b'tree'   : GitTree,
                b'tag'    : GitTag,
                b'blob'   : GitBlob
            }[fmt]
        except KeyError:
            raise Exception("Unknown type %s for object %s" % (fmt.decode("ascii"), hash))

        y = raw.find(b'\x00', x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw)-y-1:
            raise Exception("Malformed object %s: bad length" % hash)

        constructor(repo, hash, raw[y:])

class GitTree(GitObject):
    leaves = None

    class Leaf(object):
        mode = None
        blob = None
        path = None

    def serialize(self):
        pass

argsp = argsubparsers.add_parser(
    "hash-object",
    aliases=["ho"],
    help="Compute object ID and optionally creates a blob from a file")

argsp.add_argument("-t",
                   metavar="type",
                   dest="type",
                   choices=["blob", "commit", "tag", "tree"],
                   default="blob",
                   help="Specify the type")

argsp.add_argument("-w",
                   dest="write",
                   action="store_true",
                   help="Actually write the object into the database")

mutex0 = argsp.add_mutually_exclusive_group(required=True)

mutex0.add_argument("--stdin",
                    action="store_true",
                    required=False,
                    help="Read from stdin instead of from a file")

mutex0.add_argument("path",
                    nargs="?",
                    help="Read object from <file>")

def cmd_hash_object(args):
    print(args)

    with sys.stdin.buffer if args.stdin else open(args.path) as i:
        obj = hash_object(args.type, i)

    if args.write:
        obj.write()

def hash_object(type, file):
    print(file.read())
