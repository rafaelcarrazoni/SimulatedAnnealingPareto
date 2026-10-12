import random
class History:

    duration : int
    payment : int

    def __init__(self, duration : int = 4, payment : int = 250) -> None:
        self.duration = duration
        self.payment = payment