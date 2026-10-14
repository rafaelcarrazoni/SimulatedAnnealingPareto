class Developer:

    max_capacity : int
    current_capacity : int
    workload : list


    def __init__(self, max_capacity: int = 40) -> None:
        if not isinstance(max_capacity, int) or isinstance(max_capacity, bool):
            raise TypeError("max_capacity must be an integer")
        if max_capacity <= 0:
            raise ValueError("max_capacity must be greater than zero")

        self.max_capacity = max_capacity
        self.current_capacity = max_capacity

        self.workload = []

    def take_job(self, history):
        if history.taken == True or history.duration > self.current_capacity:
            return
        self.workload.append(history)
        self.current_capacity = self.current_capacity - history.duration
        history.taken = True
        