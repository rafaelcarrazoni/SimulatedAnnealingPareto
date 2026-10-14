from .blacksmith import Blacksmith
from .comparison import Comparison
from .developer import Developer
from .export import Export
from .history import History


def main() -> None:
    team = [
        Developer(max_capacity=32),
        Developer(max_capacity=40),
        Developer(max_capacity=36),
        Developer(max_capacity=28),
    ]
    histories = [
        History(id=0, duration=8, payment=500),
        History(id=1, duration=12, payment=750),
        History(id=2, duration=6, payment=400),
        History(id=3, duration=10, payment=650),
        History(id=4, duration=14, payment=900),
        History(id=5, duration=4, payment=250),
        History(id=6, duration=9, payment=550),
        History(id=7, duration=7, payment=450),
        History(id=8, duration=11, payment=700),
        History(id=9, duration=5, payment=300),
    ]

    blacksmith = Blacksmith()
    blacksmith.anneal(team, histories)
    blacksmith_path = Export.export(blacksmith)

    comparison = Comparison(seed=42)
    comparison.search(team, histories)
    comparison_path = Export.export(comparison)

    print(f"Blacksmith: {len(blacksmith.solutions)} solutions -> {blacksmith_path}")
    print(f"Comparison: {len(comparison.solutions)} solutions -> {comparison_path}")


if __name__ == "__main__":
    main()
