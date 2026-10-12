import copy

class Blacksmith:

    temperature : float
    alpha : float
    solutions : list


    def initial_solution(self, team : list, histories : list) -> list:
        for developer in team:
            for history in histories:
                developer.take_job()
            