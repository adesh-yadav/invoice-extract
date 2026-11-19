from pathlib import Path
from src.modules.extraction.domain.cdr import CDR
from src.modules.extraction.domain.exceptions import ExtractionError


class LocalCDRStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def read(self, reference: str) -> CDR:
        path = Path(reference).resolve()
        if self.root not in path.parents or path.name != "cdr-v1.json" or not path.is_file():
            raise ExtractionError("CDR_NOT_FOUND", 404)
        return CDR.model_validate_json(path.read_text())
