import argparse
from compare import FileComparer
from provenance import ProvenanceChecker
import json

from report import report_changes


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare two snapshots of files and try to determine provenance of modified files."
        )
    )
    parser.add_argument("-o", "--old")
    parser.add_argument("-n", "--new")
    parser.add_argument("-r", "--report")

    args = parser.parse_args()
    config = json.load(open("config.json"))
    provenance_checker = ProvenanceChecker(args.new, config)

    print(f"Comparing {args.old} and {args.new}...")
    comparer = FileComparer(args.old, args.new)
    changes = comparer.compare()
    print(f"Changes: {len(changes)}")
    report_changes(args.report, changes, provenance_checker)


if __name__ == "__main__":
    main()
