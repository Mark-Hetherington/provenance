import os
import pathlib
import tempfile
from git import Repo
from git.objects.commit import Commit

from provenance import ProvenanceSource, ProvenanceResult
from typing import Optional


def find_commits_modifying_file(repo, filename):
    """
    Finds all commits that modify a specified file in the given repository.

    Args:
        repo: A git.Repo object representing the Git repository.
        filename: The name of the file to track changes for.

    Returns:
        A list of git.Commit objects that modified the file.
    """
    return repo.iter_commits(paths=filename)


def get_matching_commit_for_file(
    repo: Repo, filename: str, disk_path: str
) -> Optional[Commit]:
    """
    Finds the commit that last modified the specified file in the given repository.

    Args:
        repo: A git.Repo object representing the Git repository.
        filename: The name of the file to track changes for.

    Returns:
        A git.Commit object that modified the file.
    """
    commits = find_commits_modifying_file(repo, filename)
    with open(disk_path, "rb") as file:
        file_content = file.read()
    for commit in commits:
        blob = commit.tree / filename
        if blob.data_stream.read() == file_content:
            return commit
    return None


class GitHubRepoSource(ProvenanceSource):
    def __init__(self, base_path: str, config: dict):
        super().__init__(base_path=base_path, config=config)
        self.repo: Optional[Repo] = None
        self.relative_path = config.get("relative_path")
        self.git_url = config.get("git_url")
        assert self.relative_path is not None, "relative_path must be set"
        self.clone_repo()

    def clone_progress(self, op_code, cur_count, max_count=None, message=""):
        print(f"Cloning: {op_code}, {cur_count}/{max_count}, {message}")

    def clone_repo(self):
        self.repo = Repo.clone_from(
            self.git_url, tempfile.mkdtemp(), depth=1, progress=self.clone_progress
        )

    def get_provenance(self, path: str) -> Optional[ProvenanceResult]:
        assert self.relative_path is not None, "relative_path must be set"
        assert self.repo is not None, "repo must be set"
        posix_path = pathlib.Path(path).as_posix()
        if self.relative_path not in posix_path:
            return None

        git_path = str(
            pathlib.PurePosixPath(posix_path).relative_to(self.relative_path)
        )
        #  Compare to git repo
        commit = get_matching_commit_for_file(
            self.repo, git_path, os.path.join(self.base_path, path)
        )
        if commit:
            return ProvenanceResult(
                "Vendor Software", f"{self.git_url}commit/{commit.hexsha}"
            )

        return None
