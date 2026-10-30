import argparse
import random
from collections.abc import Callable
from dataclasses import asdict
from uuid import uuid4

from .blacksmith import Blacksmith
from .comparison import Comparison
from .config import DEFAULT_SEED, SimulationConfig
from .developer import Developer
from .export import Export
from .history import History


def main(
    seed: int | None = DEFAULT_SEED,
    config: SimulationConfig | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> None:
    settings = config or SimulationConfig()
    random_generator = random.Random(seed)
    work_per_run = settings.annealing_iterations + settings.comparison_evaluations
    total_work = settings.solutions * work_per_run
    for solution_number in range(1, settings.solutions + 1):
        run_offset = (solution_number - 1) * work_per_run
        run_metadata: dict[str, object] = {
            "run_id": uuid4().hex,
            "run_index": solution_number,
            "configuration": asdict(settings),
        }
        team = [
            Developer(
                max_capacity=random_generator.randint(
                    settings.min_developer_capacity,
                    settings.max_developer_capacity,
                )
            )
            for _ in range(settings.team_size)
        ]
        histories = [
            History(
                id=history_id,
                duration=random_generator.randint(
                    settings.min_history_duration,
                    settings.max_history_duration,
                ),
                payment=random_generator.randint(
                    settings.min_history_payment,
                    settings.max_history_payment,
                ),
            )
            for history_id in range(settings.history_count)
        ]

        blacksmith = Blacksmith(
            temperature=settings.temperature,
            alpha=settings.alpha,
            max_iterations=settings.max_iterations,
            minimum_temperature=settings.minimum_temperature,
            seed=random_generator.getrandbits(64),
        )
        if progress_callback is None:
            blacksmith.anneal(team, histories)
        else:
            blacksmith.anneal(
                team,
                histories,
                progress_callback=lambda completed, _: progress_callback(
                    run_offset + completed,
                    total_work,
                    f"Execução {solution_number}/{settings.solutions} · Blacksmith",
                ),
            )
        blacksmith_path = Export.export(blacksmith, run_metadata=run_metadata)

        comparison = Comparison(
            n_evaluations=settings.comparison_evaluations,
            seed=random_generator.getrandbits(64),
        )
        if progress_callback is None:
            comparison.search(team, histories)
        else:
            comparison.search(
                team,
                histories,
                progress_callback=lambda completed, _: progress_callback(
                    run_offset + settings.annealing_iterations + completed,
                    total_work,
                    f"Execução {solution_number}/{settings.solutions} · Busca aleatória",
                ),
            )
        comparison_path = Export.export(comparison, run_metadata=run_metadata)

        print(
            f"Run {solution_number}/{settings.solutions} - "
            f"Blacksmith: {len(blacksmith.solutions)} solutions -> {blacksmith_path}"
        )
        print(
            f"Run {solution_number}/{settings.solutions} - "
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
