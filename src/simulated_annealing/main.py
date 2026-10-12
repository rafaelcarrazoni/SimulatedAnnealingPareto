    def _random_team(self) -> None:
        for _ in range(0, self.team_size):

            max_time : int = random.randint(self.min_time, self.max_time)
            self.developers.append(
                {
                    "max_time" : max_time,
                    "free_time" : max_time,
                    "workload" : []
                })

    developers : list[dict]
    team_size : int
    max_time : int
    min_time : int


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

               histories : list[dict]
                amount : int
                max_required_time : int
                min_required_time : int
            
                max_payment : int
                min_payment : int
            