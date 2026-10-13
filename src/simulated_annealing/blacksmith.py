import copy
import math
import random

from .developer import Developer
from .history import History, get_history_id


class Blacksmith:
    def __init__(
        self,
        temperature: float = 1.0,
        alpha: float = 0.99,
        max_iterations: int = 1_000,
        minimum_temperature: float = 0.01,
    ) -> None:
        if temperature <= 0:
            raise ValueError("temperature must be greater than zero")
        if not 0 < alpha < 1:
            raise ValueError("alpha must be between zero and one")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be greater than zero")
        if minimum_temperature <= 0:
            raise ValueError("minimum_temperature must be greater than zero")

        self.temperature = temperature
        self._configured_temperature = temperature
        self.alpha = alpha
        self.max_iterations = max_iterations
        self.minimum_temperature = minimum_temperature
        self.solutions: list[list[Developer]] = []
        self._histories: list[History] = []

    def anneal(
        self, team: list[Developer], histories: list[History]
    ) -> list[list[Developer]]:
        """Return the archive of non-dominated feasible assignments."""
        current = self.initial_solution(team, histories)
        self.solutions = [copy.deepcopy(current)]
        self.temperature = self._initial_temperature

        for _ in range(self.max_iterations):
            if self.temperature <= self.minimum_temperature:
                break

            neighbor = self.get_neighbor(current)
            current_objectives = self._objectives(current)
            neighbor_objectives = self._objectives(neighbor)
            self._add_to_archive(neighbor)

            if self._should_accept(current_objectives, neighbor_objectives):
                current = neighbor

            self.temperature *= self.alpha

        return self.solutions

    @property
    def _initial_temperature(self) -> float:
        return self._configured_temperature

    @_initial_temperature.setter
    def _initial_temperature(self, value: float) -> None:
        self._configured_temperature = value

    def initial_solution(
        self, team0: list[Developer], histories0: list[History]
    ) -> list[Developer]:
        """Build a randomized feasible assignment without changing the inputs."""
        team = copy.deepcopy(team0)
        self._histories = copy.deepcopy(histories0)
        history_ids = [get_history_id(history) for history in self._histories]
        if len(history_ids) != len(set(history_ids)):
            raise ValueError("history IDs must be unique")

        for developer in team:
            developer.current_capacity = developer.max_capacity
            developer.workload = []

        for history in self._histories:
            history.taken = False

        random.shuffle(self._histories)
        for history in self._histories:
            available = [
                developer
                for developer in team
                if history.duration <= developer.current_capacity
            ]
            if available:
                random.choice(available).take_job(history)

        return team

    def get_neighbor(self, solution: list[Developer]) -> list[Developer]:
        """Return a feasible assignment one add, removal, or move from solution."""
        neighbor = copy.deepcopy(solution)
        assignments = [
            (developer_index, history)
            for developer_index, developer in enumerate(neighbor)
            for history in developer.workload
        ]
        assigned_ids = {get_history_id(history) for _, history in assignments}
        unassigned = [
            history
            for history in self._histories
            if get_history_id(history) not in assigned_ids
        ]

        add_choices = [
            history
            for history in unassigned
            if any(
                history.duration <= developer.current_capacity
                for developer in neighbor
            )
        ]
        move_choices = [
            (developer_index, history, target_index)
            for developer_index, history in assignments
            for target_index, target in enumerate(neighbor)
            if target_index != developer_index
            and history.duration <= target.current_capacity
        ]

        actions = []
        if assignments:
            actions.append("remove")
        if move_choices:
            actions.append("move")
        if add_choices:
            actions.append("add")
        if not actions:
            return neighbor

        action = random.choice(actions)
        if action == "remove":
            developer_index, history = random.choice(assignments)
            developer = neighbor[developer_index]
            developer.workload.remove(history)
            developer.current_capacity += history.duration
            history.taken = False
        elif action == "move":
            developer_index, history, target_index = random.choice(move_choices)
            source = neighbor[developer_index]
            source.workload.remove(history)
            source.current_capacity += history.duration
            history.taken = False
            neighbor[target_index].take_job(history)
        else:
            history = copy.deepcopy(random.choice(add_choices))
            history.taken = False
            available = [
                developer
                for developer in neighbor
                if history.duration <= developer.current_capacity
            ]
            random.choice(available).take_job(history)

        return neighbor

    def _objectives(self, solution: list[Developer]) -> tuple[int, float]:
        business_value = sum(
            history.payment
            for developer in solution
            for history in developer.workload
        )
        occupancy_rates = [
            (developer.max_capacity - developer.current_capacity)
            / developer.max_capacity
            if developer.max_capacity > 0
            else 0.0
            for developer in solution
        ]
        imbalance = (
            max(occupancy_rates) - min(occupancy_rates)
            if occupancy_rates
            else 0.0
        )
        return business_value, imbalance

    @staticmethod
    def _dominates(
        first: tuple[int, float], second: tuple[int, float]
    ) -> bool:
        """Whether first is no worse in either objective and better in one."""
        return (
            first[0] >= second[0]
            and first[1] <= second[1]
            and (first[0] > second[0] or first[1] < second[1])
        )

    def _add_to_archive(self, candidate: list[Developer]) -> None:
        candidate_objectives = self._objectives(candidate)
        if any(
            self._dominates(self._objectives(solution), candidate_objectives)
            for solution in self.solutions
        ):
            return

        candidate_key = self._solution_key(candidate)
        if any(
            self._solution_key(solution) == candidate_key
            for solution in self.solutions
        ):
            return

        self.solutions = [
            solution
            for solution in self.solutions
            if not self._dominates(candidate_objectives, self._objectives(solution))
        ]
        self.solutions.append(copy.deepcopy(candidate))

    def _should_accept(
        self, current: tuple[int, float], candidate: tuple[int, float]
    ) -> bool:
        if self._dominates(candidate, current):
            return True
        if not self._dominates(current, candidate):
            return True

        value_scale = max(
            1,
            sum(max(0, history.payment) for history in self._histories),
        )
        imbalance_scale = 1.0
        loss = (
            (current[0] - candidate[0]) / value_scale
            + (candidate[1] - current[1]) / imbalance_scale
        )
        return random.random() < math.exp(-loss / self.temperature)

    @staticmethod
    def _solution_key(solution: list[Developer]) -> tuple:
        return tuple(
            tuple(
                sorted(
                    get_history_id(history)
                    for history in developer.workload
                )
            )
            for developer in solution
        )
