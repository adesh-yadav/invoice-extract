class ExtractionError(Exception):
    def __init__(self, code: str, http_status: int):
        self.code = code
        self.http_status = http_status
        super().__init__(code)
