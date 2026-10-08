class DomainError(Exception):

    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "내부 오류가 발생했습니다."

    def __init__(self, message: str | None = None, details: dict | None = None) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)

class EventNotFoundError(DomainError):
    code = "EVENT_NOT_FOUND"
    status_code = 404
    message = "공연이 존재하지 않습니다."

class SeatNotFoundError(DomainError):
    code = "SEAT_NOT_FOUND"
    status_code = 404
    message = "해당 공연에 존재하지 않는 좌석 번호입니다."