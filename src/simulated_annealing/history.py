class History:

    id : int
    duration : int
    payment : int
    taken : bool

    def __init__(
        self, id: int, duration: int = 4, payment: int = 250
    ) -> None:
        for name, value in (("id", id), ("duration", duration), ("payment", payment)):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be an integer")
        if duration <= 0:
            raise ValueError("duration must be greater than zero")
        if payment < 0:
            raise ValueError("payment must be non-negative")

        self.id = id
        self.duration = duration
        self.payment = payment
        self.taken = False

    def get_history_id(self) -> int:
        history_id = getattr(self, "id", None)
        if not isinstance(history_id, int):
            raise ValueError("every history must have an integer ID")
        return history_id