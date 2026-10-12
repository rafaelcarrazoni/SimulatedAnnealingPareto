import copy
from team import Team
from history import History

class Blacksmith:

    temperature : float
    alpha : float

    solutions : list[list[dict]]

    team : Team = Team()
    history : History = History()

    def anneal(self):
        pass
    def create_neighbor(self):
        pass
    def is_dominant(self):
        pass
    def create_initial_solution(self):
        developers = copy.deepcopy(Blacksmith.team.developers) 
        for developer in Blacksmith.team.developers:
            for history in Blacksmith.history.histories:
                pass
        return developers