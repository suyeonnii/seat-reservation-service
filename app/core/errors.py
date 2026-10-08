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

class UserNotFoundError(DomainError):
    code = "USER_NOT_FOUND"
    status_code = 404
    message = "사용자를 찾을 수 없습니다."


class HoldNotFoundError(DomainError):
    code = "HOLD_NOT_FOUND"
    status_code = 404
    message = "홀드를 찾을 수 없습니다."


class NotOwnerError(DomainError):
    code = "NOT_OWNER"
    status_code = 403
    message = "본인의 리소스가 아닙니다."


class SeatUnavailableError(DomainError):
    code = "SEAT_UNAVAILABLE"
    status_code = 409
    message = "이미 선점되었거나 예약된 좌석이 있습니다."


class SeatLimitExceededError(DomainError):
    code = "SEAT_LIMIT_EXCEEDED"
    status_code = 409
    message = "한 공연에서 보유 가능한 좌석 수를 초과합니다."


class EventStartedError(DomainError):
    code = "EVENT_STARTED"
    status_code = 409
    message = "이미 시작된 공연입니다."


class HoldConvertedError(DomainError):
    code = "HOLD_CONVERTED"
    status_code = 409
    message = "이미 예약으로 전환된 홀드입니다."

class HoldExpiredError(DomainError):
    code = "HOLD_EXPIRED"
    status_code = 409
    message = "만료된 홀드입니다."


class HoldNotActiveError(DomainError):
    code = "HOLD_NOT_ACTIVE"
    status_code = 409
    message = "취소된 홀드입니다."


class ReservationNotFoundError(DomainError):
    code = "RESERVATION_NOT_FOUND"
    status_code = 404
    message = "예약을 찾을 수 없습니다."