import random
class History:

    histories : list[dict]
    amount : int
    max_required_time : int
    min_required_time : int

    max_payment : int
    min_payment : int

    
    def __init__(self, amount : int = 20, max_required_time : int = 40, min_required_time : int = 2, max_payment : int = 500, min_payment : int = 100) -> None:
        self.amount = amount

        self.max_required_time = max_required_time
        self.min_required_time = min_required_time

        self.min_payment = min_payment
        self.max_payment = max_payment

        self._random_histories()

    def _random_histories(self):
        for i in range(0, self.amount):
            history_time : int = random.randint(self.min_required_time, self.max_required_time)
            payment : int = random.randint(self.min_payment, self.max_payment)

            self.histories.append(
                {"id" : i,
                 "required_time" : history_time,
                 "payment" : payment,
                 "taken" : False
                 })
