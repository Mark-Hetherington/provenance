from typing import List

from abc import ABC, abstractmethod
import os
import filecmp
import difflib


class FileChange(ABC):
    """Represents a file that has been changed between old and new snapshots"""

    def __init__(self, old_root: str, new_root: str, path: str):
        self.old_root = old_root
        self.new_root = new_root
        self.path = path

    @abstractmethod
    def modifications(self) -> str:
        pass

    def current_file_path(self) -> str:
        return os.path.join(self.new_root, self.path)


class FileRemoved(FileChange):
    """Represents a file that has been deleted from old snapshot"""

    def modifications(self) -> str:
        return "File Removed"


class FileAdded(FileChange):
    """Represents a file that has been added in old snapshot"""

    def modifications(self) -> str:
        return "File Added"


class FileModified(FileChange):
    """Represents a file that has been added in old snapshot"""

    def modifications(self) -> str:
        # diff the files and find how many sections are different
        try:
            with open(os.path.join(self.old_root, self.path), "r") as old_file:
                with open(os.path.join(self.new_root, self.path), "r") as new_file:
                    differences = list(
                        difflib.unified_diff(old_file.readlines(), new_file.readlines())
                    )
                    return str(len(differences))
        except UnicodeDecodeError:
            return "Binary files differ"


class FileComparer:
    def __init__(self, old_path, new_path):
        self.old_path = old_path
        self.new_path = new_path

    def walk_files(self):
        self.old_files = []
        self.new_files = []
        for root, _dirs, files in os.walk(self.old_path):
            for file in files:
                self.old_files.append(
                    os.path.relpath(os.path.join(root, file), self.old_path)
                )

        for root, _dirs, files in os.walk(self.new_path):
            for file in files:
                self.new_files.append(
                    os.path.relpath(os.path.join(root, file), self.new_path)
                )

        print(f"Old files: {len(self.old_files)}")
        print(f"New files: {len(self.new_files)}")

    def added_files(self):
        return set(self.new_files) - set(self.old_files)

    def removed_files(self):
        return set(self.old_files) - set(self.new_files)

    def common_files(self):
        return set(self.old_files) & set(self.new_files)

    def modified_files(self):
        print(f"Comparing {len(self.common_files())} files...")
        for index, file in enumerate(self.common_files()):
            if index % 1000 == 0:
                print(f"Compared {index} files...")
            if filecmp.cmp(
                os.path.join(self.old_path, file),
                os.path.join(self.new_path, file),
                False,
            ):
                continue
            yield file

    def compare(self) -> List[FileChange]:
        self.walk_files()
        changes: list[FileChange] = []
        changes.extend(
            [
                FileAdded(self.old_path, self.new_path, file)
                for file in self.added_files()
            ]
        )
        changes.extend(
            [
                FileRemoved(self.old_path, self.new_path, file)
                for file in self.removed_files()
            ]
        )
        changes.extend(
            [
                FileModified(self.old_path, self.new_path, file)
                for file in self.modified_files()
            ]
        )
        return changes
