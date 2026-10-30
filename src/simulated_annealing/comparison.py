import copy
import random
from collections.abc import Callable

from .config import COMPARISON_EVALUATIONS
from .developer import Developer
from .history import History


class Comparison:
    """Random feasible-search baseline for the simulated annealing algorithm."""

    def __init__(
        self,
        n_evaluations: int = COMPARISON_EVALUATIONS,
        seed: int | None = None,
    ) -> None:
        if n_evaluations <= 0:
            raise ValueError("n_evaluations must be greater than zero")

        self.n_evaluations = n_evaluations
        self.evaluations_completed = 0
        self._random = random.Random(seed)
        self.solutions: list[list[Developer]] = []

    def search(
        self,
        team: list[Developer],
        histories: list[History],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[list[Developer]]:
        """Return the non-dominated feasible assignments found at random."""
        history_ids = [history.get_history_id() for history in histories]
        if len(history_ids) != len(set(history_ids)):
            raise ValueError("history IDs must be unique")

        self.solutions = []
        self.evaluations_completed = 0
        for evaluation in range(1, self.n_evaluations + 1):
            candidate = self._random_solution(team, histories)
            self._add_to_archive(candidate)
            if progress_callback is not None:
                progress_callback(evaluation, self.n_evaluations)
            self.evaluations_completed = evaluation

        return sorted(self.solutions, key=lambda solution: self.evaluate(solution)[0])

    @staticmethod
    def evaluate(solution: list[Developer]) -> tuple[int, float]:
        """Return (business value, occupancy imbalance) for an assignment."""
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
        return (
            first[0] >= second[0]
            and first[1] <= second[1]
            and (first[0] > second[0] or first[1] < second[1])
        )

    def _random_solution(
        self, team: list[Developer], histories: list[History]
    ) -> list[Developer]:
        solution = copy.deepcopy(team)
        remaining_histories = copy.deepcopy(histories)

        for developer in solution:
            developer.current_capacity = developer.max_capacity
            developer.workload = []
        for history in remaining_histories:
            history.taken = False

        self._random.shuffle(remaining_histories)
        for history in remaining_histories:
            available = [
                developer
                for developer in solution
                if history.duration <= developer.current_capacity
            ]
            if available:
                self._random.choice(available).take_job(history)

        return solution

    def _add_to_archive(self, candidate: list[Developer]) -> None:
        candidate_objectives = self.evaluate(candidate)
        if any(
            self._dominates(self.evaluate(solution), candidate_objectives)
            or self.evaluate(solution) == candidate_objectives
            for solution in self.solutions
        ):
            return

        self.solutions = [
            solution
            for solution in self.solutions
            if not self._dominates(candidate_objectives, self.evaluate(solution))
        ]
        self.solutions.append(candidate)
