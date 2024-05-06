import hashlib
from io import BytesIO
import os
import pathlib
from typing import Dict, Optional
from zipfile import ZipFile
from provenance import ProvenanceResult, ProvenanceSource
import requests


class WordpressPluginSource(ProvenanceSource):
    def __init__(self, base_path: str, config: dict):
        super().__init__(base_path=base_path, config=config)
        self.relative_path = config.get("relative_path")
        assert self.relative_path is not None, "relative_path must be set"
        self.plugin_checksums: Dict[str, Optional[Dict[str, str]]] = {}

    def get_plugin_download(self, slug: str) -> Optional[BytesIO]:
        plugin_url = f"https://downloads.wordpress.org/plugin/{slug}.latest-stable.zip"
        print(f"Downloading plugin from {plugin_url}...")
        response = requests.get(plugin_url, allow_redirects=True)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None

    def get_plugin_checksums(self, zip_content: BytesIO) -> Dict[str, str]:
        checksums = {}
        with ZipFile(zip_content) as zip_file:
            for file in zip_file.namelist():
                with zip_file.open(file) as f:
                    hasher = hashlib.md5()
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                    checksums[file] = hasher.hexdigest()
        return checksums

    def get_plugin_data(self, slug: str) -> Optional[Dict[str, str]]:
        if slug not in self.plugin_checksums:
            # Check if plugin exists at standard URL
            print(f"Downloading plugin {slug}...")
            zip_content = self.get_plugin_download(slug)
            if zip_content is None:
                print("Not found!")
                self.plugin_checksums[slug] = None
            else:
                checksums = self.get_plugin_checksums(zip_content)
                self.plugin_checksums[slug] = checksums
        return self.plugin_checksums.get(slug, None)

    def get_provenance(self, path: str) -> Optional[ProvenanceResult]:
        assert self.relative_path is not None, "relative_path must be set"
        posix_path = pathlib.Path(path).as_posix()
        if not posix_path.startswith(self.relative_path):
            return None
        posix_path = posix_path.replace(self.relative_path + "/", "")
        plugin_slug = posix_path.split("/")[0]
        plugin_checksums = self.get_plugin_data(plugin_slug)
        if plugin_checksums is None:
            return None

        # Check if the file has the same checksum as the plugin file
        # If it does, return the plugin as the source
        # Otherwise, return None
        checksum = plugin_checksums.get(posix_path)
        if checksum:
            # Calculate disk file checksum
            disk_path = os.path.join(self.base_path, path)
            with open(disk_path, "rb") as file:
                hasher = hashlib.md5()
                for chunk in iter(lambda: file.read(4096), b""):
                    hasher.update(chunk)
                disk_checksum = hasher.hexdigest()
            if disk_checksum == checksum:
                return ProvenanceResult(
                    "Vendor Source", f"https://wordpress.org/plugins/{plugin_slug}/"
                )
        return None
