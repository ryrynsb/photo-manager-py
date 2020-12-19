import os
import sys
import util


if __name__ == "__main__":
    parser = util.get_arg_parser("deduper")
    (_options, _args) = parser.parse_args()

    if _options.root is None:
        sys.exit("parameter root is required")

    deduper = util.Deduplicator(debug=_options.debug, dry_run=_options.dry_run)
    for root, dirs, files in os.walk(_options.root, topdown=True):
        # skip excluded directories
        dirs[:] = [d for d in dirs if d not in util.EXCLUDE_DIRS]
        dirs.sort()
        for f in files:
            # skip excluded files
            if f in util.EXCLUDE_FILES:
                continue

            src = os.path.join(root, f)
            deduper.deduplicate(f, src)

    print("duplicates:")
    for f in deduper.duplicate_file_infos:
        for fi in deduper.duplicate_file_infos[f]:
            print("%s: %s - %s" % (f, fi.file_path, fi.md5))
