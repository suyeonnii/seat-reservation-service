import itertools
import random

from locust import HttpUser, between, task
from locust.exception import StopUser

from loadtest import constants as c

_user_id_counter = itertools.count()


class SeatGrabber(HttpUser):
    """시나리오 A: 좌석 오버부킹"""
    wait_time = between(0, 0)

    def on_start(self) -> None:
        idx = next(_user_id_counter) % len(c.USERS_A)
        user_id = c.USERS_A[idx]
        seat_no = random.choice(c.SEATS_A)

        self.client.post(
            f"/events/{c.EVENT_ID}/holds",
            json={"seat_nos": [seat_no]},
            headers={"X-User-Id": user_id},
            name="/events/[id]/holds (A 좌석쟁탈전)",
        )
        raise StopUser()

    @task
    def noop(self) -> None:
        pass
