from csv import writer
from typing import List

from compare import FileChange, FileRemoved
from provenance import ProvenanceChecker


def report_changes(
    report_path: str, changes: List[FileChange], provenance_checker: ProvenanceChecker
):

    with open(report_path, "w", newline="", encoding="utf-8") as report_file:
        csv_writer = writer(report_file)
        csv_writer.writerow(["File", "Changes", "Source", "Additional Info"])
        for change in changes:
            if isinstance(change, FileRemoved):
                csv_writer.writerow(
                    [
                        change.path,
                        change.modifications(),
                        "File Deleted",
                        "",
                    ]
                )
            else:
                source = provenance_checker.find_provenance(change.path)
                csv_writer.writerow(
                    [
                        change.path,
                        change.modifications(),
                        source.type,
                        source.additional_info,
                    ]
                )
