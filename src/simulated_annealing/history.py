import random


class History:

    id : int
    duration : int
    payment : int
    taken : bool

    def __init__(self, duration : int = 4, payment : int = 250) -> None:
        self.duration = duration
        self.payment = payment
        self.taken = False

    def get_history_id(self) -> int:
        history_id = getattr(self, "id", None)
        if not isinstance(history_id, int):
            raise ValueError("every history must have an integer ID")
        return history_id