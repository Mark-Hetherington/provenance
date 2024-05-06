from typing import List, Optional
from abc import ABC, abstractmethod
import importlib


class ProvenanceResult:
    def __init__(self, provenance_type: str, additional_info: str):
        self.type = provenance_type
        self.additional_info = additional_info


class ProvenanceSource(ABC):
    def __init__(self, base_path: str, config: dict):
        self.base_path = base_path
        self.config = config

    @abstractmethod
    def get_provenance(self, path: str) -> Optional[ProvenanceResult]:
        pass


class ProvenanceChecker:
    def __init__(self, base_path: str, configuration: dict):
        self.configuration = configuration
        self.base_path = base_path
        self.sources: List[ProvenanceSource] = []
        self.load_sources()

    def load_sources(self):
        for source in self.configuration["sources"]:
            if "enabled" in source and not source["enabled"]:
                continue
            print(f"Loading source: {source['name']}...")
            # import and Instantiate the source
            source_class_name = source["class"]
            module_name = ".".join(source_class_name.split(".")[:-1])
            source_module = importlib.import_module(module_name)
            source_class = getattr(source_module, source_class_name.split(".")[-1])
            source_instance = source_class(self.base_path, source["config"])
            self.sources.append(source_instance)
            print("Done!")

    def find_provenance(self, path: str) -> ProvenanceResult:
        for source in self.sources:
            provenance = source.get_provenance(path)
            if provenance:
                return provenance
        return ProvenanceResult("Unknown", "")
