import random
class Team:

    developers : list[dict]
    team_size : int
    max_time : int
    min_time : int

    def __init__(self, team_size : int = 10, max_time : int = 40, min_time : int = 20) -> None:
        self.team_size = team_size
        self.max_time = max_time
        self.min_time = min_time

        self._random_team()

    def _random_team(self) -> None:
        for _ in range(0, self.team_size):

            max_time : int = random.randint(self.min_time, self.max_time)
            self.developers.append(
                {
                    "max_time" : max_time,
                    "free_time" : max_time,
                    "workload" : []
                })

    def take_job(self, histories : list[dict], developer : int, history : int):
        pass