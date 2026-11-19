from dataclasses import dataclass


@dataclass(frozen=True)
class StoredFile:
    id: str
    status: str
    extension: str
