import argparse
import random

from .blacksmith import Blacksmith
from .comparison import Comparison
from .config import (
    DEFAULT_SEED,
    HISTORY_COUNT,
    MAX_DEVELOPER_CAPACITY,
    MAX_HISTORY_DURATION,
    MAX_HISTORY_PAYMENT,
    MIN_DEVELOPER_CAPACITY,
    MIN_HISTORY_DURATION,
    MIN_HISTORY_PAYMENT,
    SOLUTIONS,
    TEAM_SIZE,
)
from .developer import Developer
from .export import Export
from .history import History


def main(seed: int | None = DEFAULT_SEED) -> None:
    random_generator = random.Random(seed)
    for solution_number in range(1, SOLUTIONS + 1):
        team = [
            Developer(
                max_capacity=random_generator.randint(
                    MIN_DEVELOPER_CAPACITY, MAX_DEVELOPER_CAPACITY
                )
            )
            for _ in range(TEAM_SIZE)
        ]
        histories = [
            History(
                id=history_id,
                duration=random_generator.randint(
                    MIN_HISTORY_DURATION, MAX_HISTORY_DURATION
                ),
                payment=random_generator.randint(
                    MIN_HISTORY_PAYMENT, MAX_HISTORY_PAYMENT
                ),
            )
            for history_id in range(HISTORY_COUNT)
        ]

        blacksmith = Blacksmith(seed=random_generator.getrandbits(64))
        blacksmith.anneal(team, histories)
        blacksmith_path = Export.export(blacksmith)

        comparison = Comparison(seed=random_generator.getrandbits(64))
        comparison.search(team, histories)
        comparison_path = Export.export(comparison)

        print(
            f"Run {solution_number}/{SOLUTIONS} - "
            f"Blacksmith: {len(blacksmith.solutions)} solutions -> {blacksmith_path}"
        )
        print(
            f"Run {solution_number}/{SOLUTIONS} - "
            f"Comparison: {len(comparison.solutions)} solutions -> {comparison_path}"
        )


def cli() -> None:
    parser = argparse.ArgumentParser(description="Run the Pareto search demo.")
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="seed for reproducible random input data and searches",
    )
    arguments = parser.parse_args()
    main(seed=arguments.seed)


if __name__ == "__main__":
    cli()
