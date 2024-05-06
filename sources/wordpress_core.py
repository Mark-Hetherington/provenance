import hashlib
from io import BytesIO
import os
import pathlib
from typing import Dict, Optional
from zipfile import ZipFile
from provenance import ProvenanceResult, ProvenanceSource
import requests


class WordpressCoreSource(ProvenanceSource):
    def __init__(self, base_path: str, config: dict):
        super().__init__(base_path=base_path, config=config)
        self.download_url = config.get(
            "download_url", "https://wordpress.org/latest.zip"
        )
        self.file_checksums: Optional[Dict[str, str]] = None
        self.get_file_data()

    def get_download(self) -> Optional[BytesIO]:
        print(f"Downloading wordpress from {self.download_url}...")
        response = requests.get(self.download_url, allow_redirects=True)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None

    def get_file_checksums(self, zip_content: BytesIO) -> Dict[str, str]:
        checksums = {}
        with ZipFile(zip_content) as zip_file:
            for file in zip_file.namelist():
                with zip_file.open(file) as f:
                    hasher = hashlib.md5()
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                    checksums[file] = hasher.hexdigest()
        return checksums

    def get_file_data(self):
        # Check if plugin exists at standard URL
        zip_content = self.get_download()
        if zip_content is None:
            print("Not found!")
        else:
            self.file_checksums = self.get_file_checksums(zip_content)

    def get_provenance(self, path: str) -> Optional[ProvenanceResult]:
        if not self.file_checksums:
            return None
        posix_path = pathlib.Path(path).as_posix()

        # Check if the file has the same checksum as the official file
        checksum = self.file_checksums.get("wordpress/" + posix_path)
        if checksum:
            # Calculate disk file checksum
            disk_path = os.path.join(self.base_path, path)
            with open(disk_path, "rb") as file:
                hasher = hashlib.md5()
                for chunk in iter(lambda: file.read(4096), b""):
                    hasher.update(chunk)
                disk_checksum = hasher.hexdigest()
            if disk_checksum == checksum:
                return ProvenanceResult("Vendor Source", "https://wordpress.org/")
        return None
