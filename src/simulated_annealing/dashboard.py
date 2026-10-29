import json
import math
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass, fields
from tkinter import ttk
from typing import TypeAlias

from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from .config import SimulationConfig
from .export import RESULTS_DIR
from .main import main as run_demo


ALGORITHMS = ("blacksmith", "comparison")
COLORS = {"blacksmith": "#5b6cff", "comparison": "#12a88a"}
DISPLAY_NAMES = {"blacksmith": "Blacksmith", "comparison": "Busca aleatória"}
BACKGROUND = "#f4f6fb"
PANEL = "#ffffff"
TEXT = "#192238"
MUTED = "#7b8498"
GRID = "#edf0f6"

CONFIG_GROUPS = (
    (
        "Recozimento simulado",
        (
            ("temperature", "Temperatura inicial", float),
            ("alpha", "Fator de resfriamento", float),
            ("max_iterations", "Iterações máximas", int),
            ("minimum_temperature", "Temperatura mínima", float),
        ),
    ),
    (
        "Instância",
        (
            ("team_size", "Desenvolvedores", int),
            ("history_count", "Histórias", int),
            ("min_developer_capacity", "Capacidade mínima", int),
            ("max_developer_capacity", "Capacidade máxima", int),
            ("min_history_duration", "Esforço mínimo", int),
            ("max_history_duration", "Esforço máximo", int),
            ("min_history_payment", "Valor mínimo", int),
            ("max_history_payment", "Valor máximo", int),
        ),
    ),
    (
        "Execuções",
        (
            ("solutions", "Número de execuções", int),
            ("comparison_evaluations", "Avaliações aleatórias", int),
        ),
    ),
)


@dataclass(frozen=True)
class SolutionPoint:
    business_value: int
    imbalance: float


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    run_index: int | None
    points: list[SolutionPoint]


ResultRecords: TypeAlias = dict[str, list[RunRecord]]


def load_results() -> ResultRecords:
    """Load objective values from the accumulated JSONL exports."""
    records: ResultRecords = {}
    for algorithm in ALGORITHMS:
        path = RESULTS_DIR / f"{algorithm}.jsonl"
        algorithm_records: list[RunRecord] = []
        if path.exists():
            with path.open(encoding="utf-8") as result_file:
                for line_number, line in enumerate(result_file, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            f"{path.name}, linha {line_number}: JSON inválido"
                        ) from error
                    algorithm_records.append(
                        _parse_record(
                            payload,
                            algorithm,
                            path.name,
                            line_number,
                            fallback_run_id=f"legacy:{len(algorithm_records) + 1}",
                        )
                    )
        records[algorithm] = algorithm_records
    return records


def _parse_record(
    payload: object,
    algorithm: str,
    filename: str,
    line_number: int,
    fallback_run_id: str,
) -> RunRecord:
    location = f"{filename}, linha {line_number}"
    if not isinstance(payload, dict) or payload.get("algorithm") != algorithm:
        raise ValueError(f"{location}: registro não corresponde a {algorithm}")

    solutions = payload.get("solutions")
    if not isinstance(solutions, list):
        raise ValueError(f"{location}: campo 'solutions' inválido")

    points: list[SolutionPoint] = []
    for solution in solutions:
        if not isinstance(solution, dict):
            raise ValueError(f"{location}: solução inválida")
        value = solution.get("business_value")
        imbalance = solution.get("imbalance")
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not isinstance(imbalance, (int, float))
            or isinstance(imbalance, bool)
            or not math.isfinite(imbalance)
            or imbalance < 0
        ):
            raise ValueError(f"{location}: objetivos da solução inválidos")
        points.append(SolutionPoint(value, float(imbalance)))
    metadata = payload.get("run_metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"{location}: campo 'run_metadata' inválido")
    run_id = metadata.get("run_id", fallback_run_id)
    if not isinstance(run_id, str) or not run_id:
        raise ValueError(f"{location}: identificador da execução inválido")
    run_index = metadata.get("run_index")
    if run_index is not None and (
        not isinstance(run_index, int) or isinstance(run_index, bool) or run_index <= 0
    ):
        raise ValueError(f"{location}: número da execução inválido")
    return RunRecord(run_id=run_id, run_index=run_index, points=points)


class Dashboard:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pareto Lab")
        self.root.geometry("1480x960")
        self.root.minsize(1180, 760)
        self.root.configure(background=BACKGROUND)
        self.records: ResultRecords = {algorithm: [] for algorithm in ALGORITHMS}
        self.messages: queue.SimpleQueue[tuple[str, int, int, str]] = (
            queue.SimpleQueue()
        )
        self.search_running = False
        self.config_vars: dict[str, tk.StringVar] = {}

        self._configure_theme()
        self._build_layout()
        self.refresh_results()

    def _configure_theme(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("TkDefaultFont", 10))
        style.configure("TFrame", background=BACKGROUND)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure(
            "Muted.Panel.TLabel", background=PANEL, foreground=MUTED
        )
        style.configure("Title.TLabel", font=("TkDefaultFont", 23, "bold"))
        style.configure("Subtitle.TLabel", foreground=MUTED)
        style.configure("Section.TLabelframe", background=PANEL, bordercolor="#e8ebf3")
        style.configure(
            "Section.TLabelframe.Label",
            background=PANEL,
            foreground="#556078",
            font=("TkDefaultFont", 9, "bold"),
        )
        style.configure(
            "TEntry",
            fieldbackground="#f7f8fc",
            bordercolor="#e2e6ef",
            padding=(8, 6),
        )
        style.configure("TButton", padding=(12, 8), borderwidth=0)
        style.configure(
            "Accent.TButton",
            background="#5b6cff",
            foreground="white",
            font=("TkDefaultFont", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#4858eb"), ("disabled", "#aeb5d8")],
            foreground=[("disabled", "#f7f8ff")],
        )
        style.configure("Secondary.TButton", background="#eef0f7", foreground=TEXT)
        style.map("Secondary.TButton", background=[("active", "#e2e6f0")])
        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor="#e9ecf5",
            background="#5b6cff",
            bordercolor="#e9ecf5",
            lightcolor="#5b6cff",
            darkcolor="#5b6cff",
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(26, 22, 26, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Pareto Lab", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Experimentos de alocação · Simulated Annealing",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.refresh_button = ttk.Button(
            header,
            text="↻  Atualizar",
            style="Secondary.TButton",
            command=self.refresh_results,
        )
        self.refresh_button.grid(row=0, column=1, rowspan=2, sticky="e")

        content = ttk.Frame(self.root, padding=(26, 6, 26, 20))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0, minsize=310)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        self._build_settings(content)
        self._build_analysis(content)

        footer = ttk.Frame(self.root, padding=(26, 0, 26, 14))
        footer.grid(row=2, column=0, sticky="ew")
        self.status = tk.StringVar(value="Carregando resultados…")
        ttk.Label(footer, textvariable=self.status, style="Subtitle.TLabel").pack(
            side="left"
        )
        ttk.Label(
            footer,
            text="Dados em results/raw/",
            style="Subtitle.TLabel",
        ).pack(side="right")

    def _build_settings(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=(16, 16))
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        ttk.Label(
            panel,
            text="Configuração",
            style="Panel.TLabel",
            font=("TkDefaultFont", 14, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Os valores se aplicam à próxima busca.",
            style="Muted.Panel.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(27, 0))

        scroll_area = ttk.Frame(panel, style="Panel.TFrame")
        scroll_area.grid(row=1, column=0, sticky="nsew", pady=(16, 8))
        scroll_area.columnconfigure(0, weight=1)
        scroll_area.rowconfigure(0, weight=1)
        canvas = tk.Canvas(
            scroll_area,
            background=PANEL,
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(scroll_area, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        form = ttk.Frame(canvas, style="Panel.TFrame", padding=(0, 0, 8, 0))
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(form_window, width=event.width),
        )
        defaults = SimulationConfig()
        row = 0
        for section_title, controls in CONFIG_GROUPS:
            section = ttk.LabelFrame(
                form,
                text=section_title,
                style="Section.TLabelframe",
                padding=(10, 7),
            )
            section.grid(row=row, column=0, sticky="ew", pady=(0, 12))
            section.columnconfigure(0, weight=1)
            row += 1
            for name, label, _ in controls:
                self._add_config_field(section, name, label, getattr(defaults, name))
        self._add_config_field(form, "seed", "Seed (opcional)", None)

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        self.run_button = ttk.Button(
            actions,
            text="▶  Executar busca",
            style="Accent.TButton",
            command=self.start_search,
        )
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(
            actions,
            text="Restaurar padrão",
            style="Secondary.TButton",
            command=self.reset_defaults,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.progress_text = tk.StringVar(value="Pronto para executar")
        ttk.Label(
            panel,
            textvariable=self.progress_text,
            style="Muted.Panel.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(14, 5))
        self.progress_bar = ttk.Progressbar(
            panel,
            mode="determinate",
            maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=4, column=0, sticky="ew")

    def _add_config_field(
        self, parent: ttk.Frame | ttk.LabelFrame, name: str, label: str, value: object
    ) -> None:
        row = parent.grid_size()[1]
        ttk.Label(parent, text=label, style="Muted.Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=(5, 3)
        )
        variable = tk.StringVar(value="" if value is None else str(value))
        self.config_vars[name] = variable
        entry = ttk.Entry(parent, textvariable=variable, width=14)
        entry.grid(row=row + 1, column=0, sticky="ew", pady=(0, 8))
        parent.columnconfigure(0, weight=1)

    def _build_analysis(self, parent: ttk.Frame) -> None:
        analysis = ttk.Frame(parent)
        analysis.grid(row=0, column=1, sticky="nsew")
        for column in range(2):
            analysis.columnconfigure(column, weight=1, uniform="metric")
        analysis.rowconfigure(2, weight=1)

        self.metric_labels: dict[str, ttk.Label] = {}
        metric_titles = (
            ("runs", "EXECUÇÕES"),
            ("solutions", "SOLUÇÕES PARETO"),
            ("best_value", "MAIOR VALOR"),
            ("best_balance", "MENOR DESEQUILÍBRIO"),
        )
        metrics = ttk.Frame(analysis)
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        for column, (key, title) in enumerate(metric_titles):
            metrics.columnconfigure(column, weight=1, uniform="cards")
            card = ttk.Frame(metrics, style="Panel.TFrame", padding=(14, 11))
            card.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else 5, 5 if column < 3 else 0),
            )
            ttk.Label(
                card,
                text=title,
                style="Muted.Panel.TLabel",
                font=("TkDefaultFont", 8, "bold"),
            ).pack(anchor="w")
            label = ttk.Label(
                card,
                text="—",
                style="Panel.TLabel",
                font=("TkDefaultFont", 17, "bold"),
            )
            label.pack(anchor="w", pady=(6, 0))
            self.metric_labels[key] = label

        ttk.Label(
            analysis,
            text=(
                "Desequilíbrio = maior ocupação − menor ocupação. "
                "Ex.: 80% vs. 60% = 20 p.p. (pontos percentuais). "
                "Cada execução usa uma instância própria; compare os algoritmos na mesma execução."
            ),
            style="Subtitle.TLabel",
            wraplength=950,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.figure = Figure(figsize=(10.7, 7.0), dpi=100, facecolor=BACKGROUND)
        self.axes = self.figure.subplots(2, 2)
        self.figure.subplots_adjust(
            left=0.075, right=0.985, top=0.96, bottom=0.09, wspace=0.30, hspace=0.38
        )
        self.canvas = FigureCanvasTkAgg(self.figure, master=analysis)
        self.canvas.get_tk_widget().grid(row=2, column=0, columnspan=2, sticky="nsew")

    def refresh_results(self) -> None:
        try:
            records = load_results()
        except (OSError, ValueError) as error:
            self.status.set(f"Erro ao carregar resultados: {error}")
            return

        self.records = records
        self._update_metrics()
        self._draw_charts()
        run_count = max(len(records[algorithm]) for algorithm in ALGORITHMS)
        point_count = sum(
            len(record.points)
            for algorithm in ALGORITHMS
            for record in records[algorithm]
        )
        self.status.set(
            f"{run_count} execuções · {point_count} soluções carregadas"
            if point_count
            else "Sem resultados. Ajuste os parâmetros e execute uma busca."
        )

    def _update_metrics(self) -> None:
        points = [
            point
            for algorithm in ALGORITHMS
            for record in self.records[algorithm]
            for point in record.points
        ]
        run_count = max(
            (len(self.records[algorithm]) for algorithm in ALGORITHMS),
            default=0,
        )
        best_value = max((point.business_value for point in points), default=None)
        best_balance = min((point.imbalance for point in points), default=None)
        self.metric_labels["runs"].configure(text=str(run_count))
        self.metric_labels["solutions"].configure(text=str(len(points)))
        self.metric_labels["best_value"].configure(
            text=self._format_value(best_value) if best_value is not None else "—"
        )
        self.metric_labels["best_balance"].configure(
            text=f"{best_balance * 100:.2f} p.p."
            if best_balance is not None
            else "—"
        )

    def _draw_charts(self) -> None:
        pareto_axis, value_axis, balance_axis, count_axis = self.axes.flat
        for axis in self.axes.flat:
            axis.clear()
            axis.set_facecolor(PANEL)
            axis.grid(axis="y", color=GRID, linewidth=0.8)
            axis.set_axisbelow(True)
            axis.tick_params(colors=MUTED, labelsize=8, length=0, pad=6)
            axis.title.set_color(TEXT)
            axis.title.set_fontsize(10)
            axis.title.set_fontweight("bold")
            axis.xaxis.label.set_color(MUTED)
            axis.yaxis.label.set_color(MUTED)
            for spine in axis.spines.values():
                spine.set_color("#e9edf4")

        all_points = [
            point
            for algorithm in ALGORITHMS
            for record in self.records[algorithm]
            for point in record.points
        ]
        for algorithm in ALGORITHMS:
            points = [
                point
                for record in self.records[algorithm]
                for point in record.points
            ]
            if points:
                pareto_axis.scatter(
                    [point.imbalance * 100 for point in points],
                    [point.business_value for point in points],
                    label=DISPLAY_NAMES[algorithm],
                    color=COLORS[algorithm],
                    alpha=0.82,
                    s=48,
                    edgecolors="white",
                    linewidths=0.8,
                )
        pareto_axis.set_title(
            "Soluções não dominadas por execução",
            loc="left",
            pad=12,
            color=TEXT,
            fontsize=10,
            fontweight="bold",
        )
        pareto_axis.set_xlabel(
            "Diferença de ocupação (pontos percentuais)", fontsize=8
        )
        pareto_axis.set_ylabel("Valor de negócio", fontsize=8)
        if all_points:
            pareto_axis.legend(frameon=False, fontsize=8, loc="best")
        else:
            self._empty_axis(pareto_axis)

        run_ids = list(
            dict.fromkeys(
                record.run_id
                for algorithm in ALGORITHMS
                for record in self.records[algorithm]
            )
        )
        positions = list(range(len(run_ids)))
        position_by_run_id = {
            run_id: position for position, run_id in enumerate(run_ids)
        }
        bar_width = 0.34
        for offset, algorithm in (
            (-bar_width / 2, "blacksmith"),
            (bar_width / 2, "comparison"),
        ):
            values = [math.nan] * len(run_ids)
            for record in self.records[algorithm]:
                values[position_by_run_id[record.run_id]] = max(
                    (point.business_value for point in record.points),
                    default=math.nan,
                )
            value_axis.bar(
                [position + offset for position in positions],
                values,
                width=bar_width,
                color=COLORS[algorithm],
                label=DISPLAY_NAMES[algorithm],
                zorder=3,
            )
        value_axis.set_title(
            "Melhor valor por execução",
            loc="left",
            pad=12,
            color=TEXT,
            fontsize=10,
            fontweight="bold",
        )
        value_axis.set_ylabel("Valor de negócio", fontsize=8)
        value_axis.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", "."))
        )
        self._set_run_ticks(value_axis, positions)
        if run_ids:
            value_axis.legend(frameon=False, fontsize=8)
        else:
            self._empty_axis(value_axis)

        for offset, algorithm in (
            (-bar_width / 2, "blacksmith"),
            (bar_width / 2, "comparison"),
        ):
            values = [math.nan] * len(run_ids)
            for record in self.records[algorithm]:
                values[position_by_run_id[record.run_id]] = min(
                    (point.imbalance * 100 for point in record.points),
                    default=math.nan,
                )
            balance_axis.bar(
                [position + offset for position in positions],
                values,
                width=bar_width,
                color=COLORS[algorithm],
                label=DISPLAY_NAMES[algorithm],
                zorder=3,
            )
        balance_axis.set_title(
            "Menor desequilíbrio por execução",
            loc="left",
            pad=12,
            color=TEXT,
            fontsize=10,
            fontweight="bold",
        )
        balance_axis.set_ylabel("Diferença de ocupação (p.p.)", fontsize=8)
        self._set_run_ticks(balance_axis, positions)
        if run_ids:
            balance_axis.legend(frameon=False, fontsize=8)
        else:
            self._empty_axis(balance_axis)

        for offset, algorithm in (
            (-bar_width / 2, "blacksmith"),
            (bar_width / 2, "comparison"),
        ):
            counts = [math.nan] * len(run_ids)
            for record in self.records[algorithm]:
                counts[position_by_run_id[record.run_id]] = len(record.points)
            count_axis.bar(
                [position + offset for position in positions],
                counts,
                width=bar_width,
                color=COLORS[algorithm],
                label=DISPLAY_NAMES[algorithm],
                zorder=3,
            )
        count_axis.set_title(
            "Soluções Pareto encontradas",
            loc="left",
            pad=12,
            color=TEXT,
            fontsize=10,
            fontweight="bold",
        )
        count_axis.set_ylabel("Quantidade", fontsize=8)
        self._set_run_ticks(count_axis, positions)
        if run_ids:
            count_axis.legend(frameon=False, fontsize=8)
        else:
            self._empty_axis(count_axis)

        self.canvas.draw_idle()

    @staticmethod
    def _set_run_ticks(axis: Axes, positions: list[int]) -> None:
        step = max(1, math.ceil(len(positions) / 12))
        ticks = positions[::step]
        if positions and ticks[-1] != positions[-1]:
            ticks.append(positions[-1])
        axis.set_xticks(ticks, [str(position + 1) for position in ticks])
        axis.set_xlabel("Execução", fontsize=8)

    @staticmethod
    def _empty_axis(axis: Axes) -> None:
        axis.text(
            0.5,
            0.5,
            "Execute uma busca para ver os dados",
            ha="center",
            va="center",
            transform=axis.transAxes,
            color=MUTED,
            fontsize=9,
        )
        axis.set_xticks([])
        axis.set_yticks([])

    @staticmethod
    def _format_value(value: int) -> str:
        return f"{value:,}".replace(",", ".")

    def _read_config(self) -> tuple[SimulationConfig, int | None]:
        value_types = {
            name: value_type
            for _, controls in CONFIG_GROUPS
            for name, _, value_type in controls
        }
        integer_values: dict[str, int] = {}
        float_values: dict[str, float] = {}
        for name, value_type in value_types.items():
            raw_value = self.config_vars[name].get().strip()
            label = next(
                label
                for _, controls in CONFIG_GROUPS
                for field_name, label, _ in controls
                if field_name == name
            )
            try:
                if value_type is int:
                    integer_values[name] = int(raw_value)
                else:
                    float_values[name] = float(raw_value)
            except ValueError as error:
                raise ValueError(f"{label}: informe um número válido.") from error

        try:
            settings = SimulationConfig(
                temperature=float_values["temperature"],
                alpha=float_values["alpha"],
                max_iterations=integer_values["max_iterations"],
                minimum_temperature=float_values["minimum_temperature"],
                team_size=integer_values["team_size"],
                min_developer_capacity=integer_values["min_developer_capacity"],
                max_developer_capacity=integer_values["max_developer_capacity"],
                history_count=integer_values["history_count"],
                min_history_duration=integer_values["min_history_duration"],
                max_history_duration=integer_values["max_history_duration"],
                min_history_payment=integer_values["min_history_payment"],
                max_history_payment=integer_values["max_history_payment"],
                solutions=integer_values["solutions"],
                comparison_evaluations=integer_values["comparison_evaluations"],
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"Configuração inválida: {error}") from error

        seed_text = self.config_vars["seed"].get().strip()
        if not seed_text:
            return settings, None
        try:
            return settings, int(seed_text)
        except ValueError as error:
            raise ValueError("Seed: informe um número inteiro.") from error

    def reset_defaults(self) -> None:
        defaults = SimulationConfig()
        for field in fields(defaults):
            self.config_vars[field.name].set(str(getattr(defaults, field.name)))
        self.config_vars["seed"].set("")
        self.status.set("Valores padrão restaurados.")

    def start_search(self) -> None:
        if self.search_running:
            return
        try:
            settings, seed = self._read_config()
        except ValueError as error:
            self.status.set(str(error))
            return

        self.search_running = True
        self.run_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.status.set("Busca em andamento · a interface continua responsiva.")
        self.progress_bar.configure(value=0)
        self.progress_text.set("Preparando busca…")

        last_reported_at = 0.0
        last_phase = ""

        def report_progress(completed: int, total: int, phase: str) -> None:
            nonlocal last_reported_at, last_phase
            now = time.monotonic()
            if (
                phase != last_phase
                or now - last_reported_at >= 0.08
                or completed >= total
            ):
                self.messages.put(("progress", completed, total, phase))
                last_reported_at = now
                last_phase = phase

        def run() -> None:
            try:
                run_demo(
                    seed=seed,
                    config=settings,
                    progress_callback=report_progress,
                )
            except Exception as error:
                self.messages.put(("error", 0, 0, str(error)))
            else:
                self.messages.put(("done", 1, 1, "Busca concluída."))

        threading.Thread(target=run, daemon=True).start()
        self.root.after(100, self._check_search)

    def _check_search(self) -> None:
        updates: list[tuple[str, int, int, str]] = []
        while True:
            try:
                updates.append(self.messages.get_nowait())
            except queue.Empty:
                break
        if not updates:
            self.root.after(100, self._check_search)
            return

        status, completed, total, message = updates[-1]
        if status == "progress":
            percentage = 100 * completed / total if total else 0
            self.progress_bar.configure(value=percentage)
            self.progress_text.set(f"{message} · {percentage:.0f}%")
            self.root.after(100, self._check_search)
            return

        self.search_running = False
        self.run_button.configure(state="normal")
        self.refresh_button.configure(state="normal")
        if status == "error":
            self.progress_text.set("Busca interrompida.")
            self.status.set(f"Falha ao executar a busca: {message}")
            return
        self.progress_bar.configure(value=100)
        self.progress_text.set("Busca concluída · 100%")
        self.refresh_results()
        self.status.set(f"{message} Gráficos atualizados.")


def cli() -> None:
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    cli()
