from pathlib import Path
from typing import Any, Dict, List

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
plt.rcParams["font.size"] = 10


class PerformanceVisualizer:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.colors = {
            "baseline": "#64748b",
            "scari": "#0d9488",
            "air": "#0ea5e9",
            "water": "#3b82f6",
            "hybrid": "#8b5cf6",
            "savings": "#1d4ed8",
            "warning": "#d97706",
            "danger": "#dc2626",
            "safe": "#16a34a",
            "background": "#ffffff",
            "text": "#111111",
            "grid": "#e5e7eb",
        }
        self.model_colors = [
            self.colors["air"],
            self.colors["water"],
            self.colors["hybrid"],
            "#f59e0b",
            "#ec4899",
            "#14b8a6",
        ]
        plt.style.use("default")
        plt.rcParams.update(
            {
                "figure.facecolor": self.colors["background"],
                "axes.facecolor": self.colors["background"],
                "axes.edgecolor": "#d1d5db",
                "axes.labelcolor": self.colors["text"],
                "xtick.color": "#6b7280",
                "ytick.color": "#6b7280",
                "text.color": self.colors["text"],
                "grid.color": self.colors["grid"],
                "grid.alpha": 0.6,
            }
        )

    def _get_color(self, model_name: str, index: int) -> str:
        lowered = model_name.lower()
        if "air" in lowered:
            return self.colors["air"]
        if "water" in lowered or "liquid" in lowered:
            return self.colors["water"]
        if "hybrid" in lowered:
            return self.colors["hybrid"]
        return self.model_colors[index % len(self.model_colors)]

    def create_comprehensive_dashboard(
        self,
        baseline_metrics: Dict[str, Any],
        model_metrics_dict: Dict[str, Dict[str, Any]],
        baseline_data: Dict[str, List[float]],
        model_data_dict: Dict[str, Dict[str, List[float]]],
        save_individual: bool = True,
    ) -> None:
        if save_individual:
            self._save_individual_charts(baseline_metrics, model_metrics_dict, baseline_data, model_data_dict)
        figure = plt.figure(figsize=(20, 12))
        grid = gridspec.GridSpec(3, 3, figure=figure, hspace=0.3, wspace=0.3)
        self._plot_power_comparison(figure.add_subplot(grid[0:2, 0]), baseline_data, model_data_dict)
        self._plot_temperature_comparison(figure.add_subplot(grid[0:2, 1]), baseline_data, model_data_dict)
        self._plot_cumulative_savings(figure.add_subplot(grid[0:2, 2]), baseline_data, model_data_dict)
        self._plot_pue_comparison(figure.add_subplot(grid[2, 0]), baseline_metrics, model_metrics_dict)
        self._plot_efficiency_metrics(figure.add_subplot(grid[2, 1]), baseline_metrics, model_metrics_dict)
        self._plot_summary_card(figure.add_subplot(grid[2, 2]), baseline_metrics, model_metrics_dict)
        figure.suptitle("SCARI Comparative Performance Report", fontsize=22, fontweight="bold", color=self.colors["text"])
        plt.savefig(
            self.output_dir / "comprehensive_dashboard.png",
            bbox_inches="tight",
            pad_inches=0.2,
            facecolor=self.colors["background"],
            dpi=300,
        )
        plt.close()

    def _save_individual_charts(self, baseline_metrics, model_metrics_dict, baseline_data, model_data_dict) -> None:
        plots = [
            (self._plot_power_comparison, (baseline_data, model_data_dict), "1_electricity_usage.png"),
            (self._plot_temperature_comparison, (baseline_data, model_data_dict), "2_thermal_safety.png"),
            (self._plot_cumulative_savings, (baseline_data, model_data_dict), "3_total_savings.png"),
            (self._plot_pue_comparison, (baseline_metrics, model_metrics_dict), "4_efficiency_score.png"),
        ]
        for plotter, args, filename in plots:
            figure, axis = plt.subplots(figsize=(10, 6))
            figure.patch.set_facecolor(self.colors["background"])
            axis.set_facecolor(self.colors["background"])
            plotter(axis, *args)
            plt.savefig(
                self.output_dir / filename,
                bbox_inches="tight",
                pad_inches=0.2,
                facecolor=self.colors["background"],
                dpi=300,
            )
            plt.close()

    def _plot_power_comparison(self, ax, baseline_data, model_data_dict) -> None:
        time = np.arange(len(baseline_data["powers"]))
        ax.plot(
            time,
            baseline_data["powers"],
            label="Baseline",
            color=self.colors["baseline"],
            linewidth=2.5,
            alpha=0.9,
        )
        for index, (model_name, model_data) in enumerate(model_data_dict.items()):
            ax.plot(
                time,
                model_data["powers"],
                label=model_name,
                color=self._get_color(model_name, index),
                linewidth=1.5,
                alpha=0.85,
            )
        ax.set_xlabel("Time Steps", fontweight="regular")
        ax.set_ylabel("Electricity Consumption (Watts)", fontweight="bold")
        ax.set_title("Power Load Comparison", fontsize=14, fontweight="bold")
        ax.legend(loc="upper right", framealpha=0.9)
        ax.grid(True, alpha=0.3)

    def _plot_temperature_comparison(self, ax, baseline_data, model_data_dict) -> None:
        time = np.arange(len(baseline_data["temps"]))
        ax.plot(time, baseline_data["temps"], label="Baseline", color=self.colors["baseline"], linewidth=2.5, alpha=0.9)
        for index, (model_name, model_data) in enumerate(model_data_dict.items()):
            ax.plot(
                time,
                model_data["temps"],
                label=model_name,
                color=self._get_color(model_name, index),
                linewidth=1.5,
                alpha=0.85,
            )
        ax.axhspan(20, 55, alpha=0.08, color=self.colors["safe"], label="Optimal (< 55C)")
        ax.axhspan(55, 60, alpha=0.08, color=self.colors["warning"], label="Sweet Spot (55-60C)")
        ax.axhspan(60, 100, alpha=0.08, color=self.colors["danger"], label="Danger (> 60C)")
        ax.axhline(60, color=self.colors["danger"], linestyle="--", linewidth=1.5, alpha=0.7, label="Safety Limit (60C)")
        ax.set_xlabel("Time Steps", fontweight="regular")
        ax.set_ylabel("Server Temperature (C)", fontweight="bold")
        ax.set_title("Thermal Safety Envelopes", fontsize=14, fontweight="bold")
        ax.legend(loc="upper left", framealpha=0.9, fontsize=8)
        ax.grid(True, alpha=0.3)
        all_temps = list(baseline_data["temps"])
        for values in model_data_dict.values():
            all_temps.extend(list(values["temps"]))
        ax.set_ylim(max(20, min(all_temps) - 5), max(all_temps) + 5)

    def _plot_cumulative_savings(self, ax, baseline_data, model_data_dict) -> None:
        baseline_cumsum = np.cumsum(baseline_data["powers"]) / 1000.0
        time = np.arange(len(baseline_cumsum))
        ax.axhline(0, color="black", linestyle="-", linewidth=1, alpha=0.3)
        for index, (model_name, model_data) in enumerate(model_data_dict.items()):
            model_cumsum = np.cumsum(model_data["powers"]) / 1000.0
            savings = baseline_cumsum - model_cumsum
            color = self._get_color(model_name, index)
            ax.plot(time, savings, label=model_name, color=color, linewidth=2)
            if len(model_data_dict) == 1:
                ax.fill_between(time, 0, savings, alpha=0.15, color=color)
        ax.set_xlabel("Time Steps", fontweight="regular")
        ax.set_ylabel("Energy Saved (kWh)", fontweight="bold")
        ax.set_title("Cumulative Energy Savings vs Baseline", fontsize=14, fontweight="bold")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

    def _plot_pue_comparison(self, ax, baseline_metrics, model_metrics_dict) -> None:
        baseline_label = baseline_metrics.get("controller_name", "Baseline")
        names = [baseline_label] + list(model_metrics_dict.keys())
        pue_values = [baseline_metrics.get("average_pue", 1.0)] + [metrics.get("average_pue", 1.0) for metrics in model_metrics_dict.values()]
        colors = [self.colors["baseline"]] + [self._get_color(name, index) for index, name in enumerate(model_metrics_dict.keys())]
        bars = ax.bar(names, pue_values, color=colors, alpha=0.8, edgecolor="black", linewidth=1)
        ax.axhline(1.0, color="green", linestyle="--", linewidth=2, label="Ideal = 1.0", alpha=0.7)
        ax.axhline(1.2, color="orange", linestyle="--", linewidth=1.5, label="Target = 1.2", alpha=0.7)
        ax.set_ylabel("PUE Score", fontweight="bold")
        ax.set_title("PUE Efficiency Comparison", fontsize=12, fontweight="bold")
        ax.set_ylim(1.0, max(pue_values) * 1.1)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
        for bar, value in zip(bars, pue_values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height(),
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=9,
            )

    def _plot_efficiency_metrics(self, ax, baseline_metrics, model_metrics_dict) -> None:
        categories = ["Power\nSavings %", "Cooling\nSavings %", "Thermal\nStability", "PUE\nScore"]
        baseline_power = baseline_metrics.get("total_power_consumption", 1.0)
        baseline_cooling = max(baseline_metrics.get("total_cooling_power_consumption", 1.0), 1e-6)

        def safe_score(value):
            return 0 if np.isnan(value) else value

        baseline_scores = [
            0,
            0,
            safe_score(baseline_metrics.get("thermal_stability", 0.0)) * 100,
            max(0, 1.5 - baseline_metrics.get("average_pue", 1.5)) * 100,
        ]
        y_pos = np.arange(len(categories))
        num_models = len(model_metrics_dict) + 1
        bar_height = 0.8 / num_models
        ax.barh(
            y_pos - bar_height * num_models / 2,
            baseline_scores,
            bar_height,
            label=baseline_metrics.get("controller_name", "Baseline"),
            color=self.colors["baseline"],
            alpha=0.8,
        )
        for index, (model_name, metrics) in enumerate(model_metrics_dict.items()):
            model_scores = [
                max(0, (baseline_power - metrics.get("total_power_consumption", baseline_power)) / baseline_power * 100),
                max(0, (baseline_cooling - metrics.get("total_cooling_power_consumption", baseline_cooling)) / baseline_cooling * 100),
                safe_score(metrics.get("thermal_stability", 0.0)) * 100,
                max(0, 1.5 - metrics.get("average_pue", 1.5)) * 100,
            ]
            offset = y_pos - bar_height * num_models / 2 + bar_height * (index + 1)
            ax.barh(offset, model_scores, bar_height, label=model_name, color=self._get_color(model_name, index), alpha=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=9)
        ax.set_xlabel("Score (%)", fontweight="bold")
        ax.set_xlim(0, 100)
        ax.set_title("Cross-Dimensional Metrics", fontsize=12, fontweight="bold")
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(axis="x", alpha=0.3)

    def _plot_summary_card(self, ax, baseline_metrics, model_metrics_dict) -> None:
        ax.axis("off")
        if not model_metrics_dict:
            return
        best_name = ""
        best_savings = -999.0
        best_pue = 999.0
        best_cooling = -999.0
        baseline_power = baseline_metrics["total_power_consumption"]
        baseline_cooling = max(baseline_metrics.get("total_cooling_power_consumption", 1.0), 1e-6)
        for model_name, metrics in model_metrics_dict.items():
            energy_savings = (baseline_power - metrics["total_power_consumption"]) / baseline_power * 100
            cooling_savings = (baseline_cooling - metrics.get("total_cooling_power_consumption", baseline_cooling)) / baseline_cooling * 100
            if energy_savings > best_savings:
                best_savings = energy_savings
                best_cooling = cooling_savings
                best_name = model_name
                best_pue = metrics.get("average_pue", 1.0)
        summary = (
            "\n        LEADERBOARD SUMMARY\n"
            "        ---------------------------\n"
            "\n"
            f"        TOP PERFORMER: {best_name.upper()}\n"
            "\n"
            f"        - Energy Savings : {best_savings:+.1f}%\n"
            f"        - Cooling Savings: {best_cooling:+.1f}%\n"
            f"        - PUE Efficiency : {best_pue:.3f}\n"
            "\n"
            f"        MODELS TESTED    : {len(model_metrics_dict)}\n"
            f"        BASELINE LABEL   : {baseline_metrics.get('controller_name', 'Baseline')}\n"
            f"        BASELINE PUE     : {baseline_metrics.get('average_pue', 1.0):.3f}\n"
            "\n"
            "        Deep comparisons are available\n"
            "        in the adjacent charts.\n"
        )
        ax.text(
            0.5,
            0.5,
            summary,
            transform=ax.transAxes,
            fontsize=10,
            ha="center",
            va="center",
            family="monospace",
            bbox=dict(
                boxstyle="round",
                facecolor=self.colors["scari"],
                alpha=0.1,
                edgecolor=self.colors["scari"],
                linewidth=1,
            ),
        )

    def create_power_breakdown_chart(self, baseline_data, model_data_dict) -> None:
        pass
