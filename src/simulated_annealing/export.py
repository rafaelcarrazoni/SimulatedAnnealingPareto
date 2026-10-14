import json
from pathlib import Path

from .blacksmith import Blacksmith
from .comparison import Comparison
from .developer import Developer


class Export:
    @staticmethod
    def export(obj: Blacksmith | Comparison) -> Path:
        if isinstance(obj, Blacksmith):
            algorithm = "blacksmith"
        elif isinstance(obj, Comparison):
            algorithm = "comparison"
        else:
            raise TypeError("obj must be a Blacksmith or Comparison instance")

        results_dir = Path(__file__).resolve().parents[2] / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = results_dir / f"{algorithm}.json"

        payload = {
            "algorithm": algorithm,
            "solutions": [
                Export._serialize_solution(solution)
                for solution in obj.solutions
            ],
        }
        with output_path.open("w", encoding="utf-8") as result_file:
            json.dump(payload, result_file, indent=2, ensure_ascii=False)
            result_file.write("\n")

        return output_path

    @staticmethod
    def _serialize_solution(solution: list[Developer]) -> dict[str, object]:
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

        return {
            "business_value": business_value,
            "imbalance": imbalance,
            "developers": [
                {
                    "max_capacity": developer.max_capacity,
                    "remaining_capacity": developer.current_capacity,
                    "assigned_hours": (
                        developer.max_capacity - developer.current_capacity
                    ),
                    "histories": [
                        {
                            "id": history.get_history_id(),
                            "duration": history.duration,
                            "payment": history.payment,
                        }
                        for history in developer.workload
                    ],
                }
                for developer in solution
            ],
        }