import os
import sys
import util


class DirectoryManager:
    def __init__(self, max_requests_per_dir, dry_run_enabled=False, debug_enabled=False):
        self.max_requests_per_dir = max_requests_per_dir
        self.debug = debug_enabled
        self.dry_run = dry_run_enabled
        self.request_count = 0

    def current_dir(self):
        current = "_new/%d" % int(1 + self.request_count / self.max_requests_per_dir)
        if self.request_count % self.max_requests_per_dir == 0:
            if self.debug:
                print("mkdirs %s" % current)
            if not self.dry_run:
                os.makedirs(current)
        self.request_count += 1
        return current


if __name__ == "__main__":
    parser = util.get_arg_parser("arranger")
    parser.add_option("-m", "--max-files-per-dir", dest="max", default=300, help="maximum files per directory")
    (_options, _args) = parser.parse_args()

    if _options.root is None:
        sys.exit("parameter root is required")
    debug = _options.debug
    dry_run = _options.dry_run

    dir_mgr = DirectoryManager(int(_options.max), dry_run_enabled=dry_run, debug_enabled=debug)
    deduper = util.Deduplicator(debug=debug, dry_run=dry_run)
    for root, dirs, files in os.walk(_options.root, topdown=True):
        # skip excluded directories
        dirs[:] = [d for d in dirs if d not in util.EXCLUDE_DIRS]
        for f in files:
            # skip excluded files
            if f in util.EXCLUDE_FILES:
                continue

            src = os.path.join(root, f)

            deduplicate, src = deduper.deduplicate(f, src)
            if deduplicate:
                print("skipping duplicate: %s" % src)
                continue

            # move the file to a folder
            dst = os.path.join(dir_mgr.current_dir(), f)
            if debug:
                print("mv %s %s" % (src, dst))
            if not dry_run:
                os.rename(src, dst)
                deduper.update(f, src, dst)
