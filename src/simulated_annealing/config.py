import math
from dataclasses import dataclass


DEFAULT_SEED: int | None = None

TEMPERATURE = 0.1
ALPHA = 0.9995
MAX_ITERATIONS = 20_000
MINIMUM_TEMPERATURE = 0.00001

TEAM_SIZE = 30
MIN_DEVELOPER_CAPACITY = 28
MAX_DEVELOPER_CAPACITY = 40

HISTORY_COUNT = 120
MIN_HISTORY_DURATION = 4
MAX_HISTORY_DURATION = 14
MIN_HISTORY_PAYMENT = 250
MAX_HISTORY_PAYMENT = 900

SOLUTIONS = 10
COMPARISON_EVALUATIONS = MAX_ITERATIONS


@dataclass(frozen=True)
class SimulationConfig:
    temperature: float = TEMPERATURE
    alpha: float = ALPHA
    max_iterations: int = MAX_ITERATIONS
    minimum_temperature: float = MINIMUM_TEMPERATURE
    team_size: int = TEAM_SIZE
    min_developer_capacity: int = MIN_DEVELOPER_CAPACITY
    max_developer_capacity: int = MAX_DEVELOPER_CAPACITY
    history_count: int = HISTORY_COUNT
    min_history_duration: int = MIN_HISTORY_DURATION
    max_history_duration: int = MAX_HISTORY_DURATION
    min_history_payment: int = MIN_HISTORY_PAYMENT
    max_history_payment: int = MAX_HISTORY_PAYMENT
    solutions: int = SOLUTIONS
    comparison_evaluations: int = COMPARISON_EVALUATIONS

    @property
    def annealing_iterations(self) -> int:
        temperature = self.temperature
        for iterations in range(self.max_iterations):
            if temperature <= self.minimum_temperature:
                return iterations
            temperature *= self.alpha
        return self.max_iterations

    def __post_init__(self) -> None:
        integer_fields = (
            "max_iterations",
            "team_size",
            "min_developer_capacity",
            "max_developer_capacity",
            "history_count",
            "min_history_duration",
            "max_history_duration",
            "min_history_payment",
            "max_history_payment",
            "solutions",
            "comparison_evaluations",
        )
        for field_name in integer_fields:
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{field_name} must be an integer")
            if value <= 0 and field_name != "min_history_payment":
                raise ValueError(f"{field_name} must be greater than zero")

        for field_name in ("temperature", "alpha", "minimum_temperature"):
            value = getattr(self, field_name)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                raise TypeError(f"{field_name} must be a finite number")

        if self.temperature <= 0 or self.minimum_temperature <= 0:
            raise ValueError("temperatures must be greater than zero")
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be between zero and one")
        if self.min_developer_capacity > self.max_developer_capacity:
            raise ValueError("minimum developer capacity exceeds maximum")
        if self.min_history_duration > self.max_history_duration:
            raise ValueError("minimum history duration exceeds maximum")
        if self.min_history_payment < 0:
            raise ValueError("minimum history payment must be non-negative")
        if self.min_history_payment > self.max_history_payment:
            raise ValueError("minimum history payment exceeds maximum")