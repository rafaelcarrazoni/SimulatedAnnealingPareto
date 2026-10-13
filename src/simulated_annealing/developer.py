import random
class Developer:

    max_capacity : int
    current_capacity : int
    workload : list


    def __init__(self, max_capacity = 40) -> None:
        self.max_capacity = max_capacity
        self.current_capacity = max_capacity

        self.workload = []

    def take_job(self, history):
        if history.taken == True or history.duration > self.current_capacity:
            return
        self.workload.append(history)
        self.current_capacity = self.current_capacity - history.duration
        history.taken = True
        