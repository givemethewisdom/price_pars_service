class CustomException(Exception):
    """Простое исключение без логирования"""

    def __init__(self, message: str, detail: str = None, status_code: int = 500):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message if not detail else f"{message}: {detail}")
