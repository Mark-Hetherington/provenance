import filecmp
import os
import pathlib
from typing import Optional
from provenance import ProvenanceResult, ProvenanceSource


class LocalFilesSource(ProvenanceSource):
    def __init__(self, base_path: str, config: dict):
        super().__init__(base_path=base_path, config=config)
        self.relative_path = config.get("relative_path")
        self.reference_path = config.get("reference_path")
        self.source_type = config.get("source_type")
        self.source_additional = config.get("source_additional")

    def get_provenance(self, path: str) -> Optional[ProvenanceResult]:
        assert self.relative_path is not None, "relative_path must be set"
        assert self.reference_path is not None, "reference_path must be set"
        assert self.source_type is not None, "source_type must be set"
        assert self.source_additional is not None, "source_additional must be set"
        posix_path = pathlib.Path(path).as_posix()
        if not posix_path.startswith(self.relative_path):
            return None
        posix_path = posix_path.replace(self.relative_path + "/", "")

        comparison_path = os.path.join(self.reference_path, posix_path)
        if not os.path.exists(comparison_path):
            return None

        file_path = os.path.join(self.base_path, path)

        if filecmp.cmp(file_path, comparison_path):
            return ProvenanceResult(self.source_type, self.source_additional)
        return None
