import matplotlib

matplotlib.use("Agg")

import shutil
import matplotlib.pyplot as plt
import pytest
from pathlib import Path

from src.utils.visualization import PerformanceVisualizer


def test_normalize_baseline_label_maps_real_world_pid():
    assert PerformanceVisualizer._normalize_baseline_label("REAL_WORLD_PID") == "BASELINE"


def test_cumulative_savings_are_reported_in_kwh():
    tmp_path = Path("tmp") / "visualizer_test"
    tmp_path.mkdir(parents=True, exist_ok=True)
    try:
        visualizer = PerformanceVisualizer(str(tmp_path))
        figure, axis = plt.subplots()

        visualizer._plot_cumulative_savings(
            axis,
            {"powers": [3600.0, 3600.0]},
            {"SCARI": {"powers": [1800.0, 1800.0]}},
        )

        savings_line = axis.lines[-1]
        assert list(savings_line.get_ydata()) == pytest.approx([0.0005, 0.0010])
        assert axis.get_ylabel() == "Energy Saved (kWh)"

        plt.close(figure)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
