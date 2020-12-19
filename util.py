import hashlib
import optparse
import os
import time

EXCLUDE_DIRS = ["iPod Photo Cache"]
EXCLUDE_FILES = ["ZbThumbnail.info", ".DS_Store"]


class FileInfo:
    def __init__(self, file_path, md5):
        self.file_path = file_path
        self.md5 = md5


class Deduplicator:
    def __init__(self, debug=False, dry_run=False):
        # unique_filenames is used to lazily calculate the md5 of the first duplicate of a file we find.
        # this helps avoid calculating the MD5 of every file, regardless of whether it has duplicates or not
        self.unique_filenames = {}
        self.duplicate_file_infos = {}
        self.debug = debug
        self.dry_run = dry_run

    @staticmethod
    def calc_md5(file_path):
        with open(file_path, 'rb') as file_to_check:
            # read contents of the file
            data = file_to_check.read()
            # pipe contents of the file through
            return hashlib.md5(data).hexdigest()

    def is_dup(self, lower_filename, new_info):
        for existing_info in self.duplicate_file_infos[lower_filename]:
            if existing_info.md5 == new_info.md5:
                return True
        return False

    def deduplicate(self, f, src):
        dup = False
        lower_filename = f.lower()
        # duplicate handling
        if lower_filename in self.unique_filenames:
            # duplicate file name
            new_info = FileInfo(src, self.calc_md5(src))
            if lower_filename in self.duplicate_file_infos:
                # we've already started a duplicate list
                pass
            else:
                self.duplicate_file_infos[lower_filename] = []
                existing_path = self.unique_filenames[lower_filename]
                existing_info = FileInfo(existing_path, self.calc_md5(existing_path))
                self.duplicate_file_infos[lower_filename].append(existing_info)
            dup = self.is_dup(lower_filename, new_info)
            if dup:
                # definitely a duplicate with same md5; delete the file
                if self.debug:
                    print("rm %s" % src)
                if not self.dry_run:
                    os.remove(src)
            else:
                # not a duplicate, but has duplicate name; rename the file
                basename = os.path.basename(src)
                dirname = os.path.dirname(src)
                split = basename.split(".")
                new_name = "%s-%.3f.%s" % (split[0], time.time(), ".".join(split[1:]))
                old_name = src
                src = os.path.join(dirname, new_name)

                if self.debug:
                    print("mv %s %s" % (old_name, src))
                if not self.dry_run:
                    os.rename(old_name, src)

            # add the duplicate file info
            self.duplicate_file_infos[lower_filename].append(new_info)
        else:
            self.unique_filenames[lower_filename] = src

        return dup, src

    # todo: kind of hacky.  Figure out a better solution?
    def update(self, f, src, dst):
        lower_filename = f.lower()
        # update unique_filenames's src
        self.unique_filenames[lower_filename] = src

        # update duplicate_file_info's src for the appropriate file (src==src) if already present
        if lower_filename in self.duplicate_file_infos:
            found = False
            for existing_info in self.duplicate_file_infos[lower_filename]:
                if existing_info.src == src:
                    existing_info.src = dst
                    found = True
                    break
            if not found:
                raise RuntimeError


def get_arg_parser(program):
    opt_parser = optparse.OptionParser(prog=program, version="%prog 1.1")
    opt_parser.add_option("-n", "--dry-run", dest="dry_run", action="store_true", default=False,
                          help="show what would have been done")
    opt_parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False, help="debug logging")
    opt_parser.add_option("-r", "--root", dest="root", help="root directory to start")

    return opt_parser
