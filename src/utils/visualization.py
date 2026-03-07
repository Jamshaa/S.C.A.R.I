import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import seaborn as sns
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 10

class PerformanceVisualizer:

    def __init__(self, output_dir: str='outputs'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.colors = {'baseline': '#64748b', 'scari': '#0d9488', 'air': '#0ea5e9', 'water': '#3b82f6', 'hybrid': '#8b5cf6', 'savings': '#1d4ed8', 'warning': '#d97706', 'danger': '#dc2626', 'safe': '#16a34a', 'background': '#ffffff', 'text': '#111111', 'grid': '#e5e7eb'}
        self.model_colors = [self.colors['air'], self.colors['water'], self.colors['hybrid'], '#f59e0b', '#ec4899', '#14b8a6']
        plt.style.use('default')
        plt.rcParams.update({'figure.facecolor': self.colors['background'], 'axes.facecolor': self.colors['background'], 'axes.edgecolor': '#d1d5db', 'axes.labelcolor': self.colors['text'], 'xtick.color': '#6b7280', 'ytick.color': '#6b7280', 'text.color': self.colors['text'], 'grid.color': self.colors['grid'], 'grid.alpha': 0.6})

    def _get_color(self, model_name: str, i: int) -> str:
        name_lower = model_name.lower()
        if 'air' in name_lower:
            return self.colors['air']
        if 'water' in name_lower or 'liquid' in name_lower:
            return self.colors['water']
        if 'hybrid' in name_lower:
            return self.colors['hybrid']
        return self.model_colors[i % len(self.model_colors)]

    def create_comprehensive_dashboard(self, baseline_metrics: Dict[str, Any], model_metrics_dict: Dict[str, Dict[str, Any]], baseline_data: Dict[str, List[float]], model_data_dict: Dict[str, Dict[str, List[float]]], save_individual: bool=True) -> None:
        if save_individual:
            self._save_individual_charts(baseline_metrics, model_metrics_dict, baseline_data, model_data_dict)
        fig = plt.figure(figsize=(20, 12))
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
        self._plot_power_comparison(fig.add_subplot(gs[0:2, 0]), baseline_data, model_data_dict)
        self._plot_temperature_comparison(fig.add_subplot(gs[0:2, 1]), baseline_data, model_data_dict)
        self._plot_cumulative_savings(fig.add_subplot(gs[0:2, 2]), baseline_data, model_data_dict)
        self._plot_pue_comparison(fig.add_subplot(gs[2, 0]), baseline_metrics, model_metrics_dict)
        self._plot_efficiency_metrics(fig.add_subplot(gs[2, 1]), baseline_metrics, model_metrics_dict)
        self._plot_summary_card(fig.add_subplot(gs[2, 2]), baseline_metrics, model_metrics_dict)
        fig.suptitle('SCARI Comparative Performance Report', fontsize=22, fontweight='bold', color=self.colors['text'])
        plt.savefig(self.output_dir / 'comprehensive_dashboard.png', bbox_inches='tight', pad_inches=0.2, facecolor=self.colors['background'], dpi=300)
        plt.close()

    def _save_individual_charts(self, bm, mm_dict, bd, md_dict):
        plots = [(self._plot_power_comparison, (bd, md_dict), '1_electricity_usage.png'), (self._plot_temperature_comparison, (bd, md_dict), '2_thermal_safety.png'), (self._plot_cumulative_savings, (bd, md_dict), '3_total_savings.png'), (self._plot_pue_comparison, (bm, mm_dict), '4_efficiency_score.png')]
        for func, args, filename in plots:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor(self.colors['background'])
            ax.set_facecolor(self.colors['background'])
            func(ax, *args)
            plt.savefig(self.output_dir / filename, bbox_inches='tight', pad_inches=0.2, facecolor=self.colors['background'], dpi=300)
            plt.close()

    def _plot_power_comparison(self, ax, baseline_data, model_data_dict):
        time = np.arange(len(baseline_data['powers']))
        ax.plot(time, baseline_data['powers'], label='Baseline (PID)', color=self.colors['baseline'], linewidth=2.5, alpha=0.9)
        for i, (m_name, m_data) in enumerate(model_data_dict.items()):
            c = self._get_color(m_name, i)
            ax.plot(time, m_data['powers'], label=f'{m_name}', color=c, linewidth=1.5, alpha=0.8)
        ax.set_xlabel('Time Steps', fontweight='regular')
        ax.set_ylabel('Electricity Consumption (Watts)', fontweight='bold')
        ax.set_title('Power Load Comparison', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)

    def _plot_temperature_comparison(self, ax, baseline_data, model_data_dict):
        time = np.arange(len(baseline_data['temps']))
        ax.plot(time, baseline_data['temps'], label='Baseline', color=self.colors['baseline'], linewidth=2.5, alpha=0.9)
        for i, (m_name, m_data) in enumerate(model_data_dict.items()):
            c = self._get_color(m_name, i)
            ax.plot(time, m_data['temps'], label=f'{m_name}', color=c, linewidth=1.5, alpha=0.8)
        ax.axhspan(20, 55, alpha=0.08, color=self.colors['safe'], label='Optimal (< 55°C)')
        ax.axhspan(55, 60, alpha=0.08, color=self.colors['warning'], label='Sweet Spot (55-60°C)')
        ax.axhspan(60, 100, alpha=0.08, color=self.colors['danger'], label='Danger (> 60°C)')
        ax.axhline(60, color=self.colors['danger'], linestyle='--', linewidth=1.5, alpha=0.7, label='Safety Limit (60°C)')
        ax.set_xlabel('Time Steps', fontweight='regular')
        ax.set_ylabel('Server Temperature (°C)', fontweight='bold')
        ax.set_title('Thermal Safety Envelopes', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9, fontsize=8)
        ax.grid(True, alpha=0.3)
        all_temps = list(baseline_data['temps'])
        for v in model_data_dict.values():
            all_temps.extend(list(v['temps']))
        ax.set_ylim(max(20, min(all_temps) - 5), max(all_temps) + 5)

    def _plot_cumulative_savings(self, ax, baseline_data, model_data_dict):
        b_cumsum = np.cumsum(baseline_data['powers']) / 1000.0
        time = np.arange(len(b_cumsum))
        ax.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)
        for i, (m_name, m_data) in enumerate(model_data_dict.items()):
            m_cumsum = np.cumsum(m_data['powers']) / 1000.0
            savings = b_cumsum - m_cumsum
            c = self._get_color(m_name, i)
            ax.plot(time, savings, label=f'{m_name}', color=c, linewidth=2)
            if len(model_data_dict) == 1:
                ax.fill_between(time, 0, savings, alpha=0.15, color=c)
        ax.set_xlabel('Time Steps', fontweight='regular')
        ax.set_ylabel('Energy Saved (kWh)', fontweight='bold')
        ax.set_title('Cumulative Energy Savings vs Baseline', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_pue_comparison(self, ax, baseline_metrics, model_metrics_dict):
        names = ['Baseline'] + list(model_metrics_dict.keys())
        pue_vals = [baseline_metrics.get('average_pue', 1.0)] + [m.get('average_pue', 1.0) for m in model_metrics_dict.values()]
        colors = [self.colors['baseline']] + [self._get_color(n, i) for i, n in enumerate(model_metrics_dict.keys())]
        bars = ax.bar(names, pue_vals, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
        ax.axhline(1.0, color='green', linestyle='--', linewidth=2, label='Ideal = 1.0', alpha=0.7)
        ax.axhline(1.2, color='orange', linestyle='--', linewidth=1.5, label='Target = 1.2', alpha=0.7)
        ax.set_ylabel('PUE Score', fontweight='bold')
        ax.set_title('PUE Efficiency Comparison', fontsize=12, fontweight='bold')
        ax.set_ylim(1.0, max(pue_vals) * 1.1)
        ax.grid(axis='y', alpha=0.3)
        ax.legend(fontsize=8)
        for bar, val in zip(bars, pue_vals):
            ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height(), f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=9)

    def _plot_efficiency_metrics(self, ax, baseline_metrics, model_metrics_dict):
        cats = ['Power\nSavings %', 'Thermal\nStability', 'PUE\nScore']
        b_pwr = baseline_metrics.get('total_power_consumption', 1)

        def safe_score(val):
            return 0 if np.isnan(val) else val
        b_scores = [0, safe_score(baseline_metrics.get('thermal_stability', 0)) * 100, max(0, 1.5 - baseline_metrics.get('average_pue', 1.5)) * 100]
        y_pos = np.arange(len(cats))
        num_models = len(model_metrics_dict) + 1
        bar_height = 0.8 / num_models
        ax.barh(y_pos - bar_height * num_models / 2, b_scores, bar_height, label='Baseline', color=self.colors['baseline'], alpha=0.8)
        for i, (m_name, m_met) in enumerate(model_metrics_dict.items()):
            m_scores = [max(0, (b_pwr - m_met.get('total_power_consumption', b_pwr)) / b_pwr * 100), safe_score(m_met.get('thermal_stability', 0)) * 100, max(0, 1.5 - m_met.get('average_pue', 1.5)) * 100]
            offset = y_pos - bar_height * num_models / 2 + bar_height * (i + 1)
            c = self._get_color(m_name, i)
            ax.barh(offset, m_scores, bar_height, label=m_name, color=c, alpha=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(cats, fontsize=9)
        ax.set_xlabel('Score (%)', fontweight='bold')
        ax.set_xlim(0, 100)
        ax.set_title('Cross-Dimensional Metrics', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(axis='x', alpha=0.3)

    def _plot_summary_card(self, ax, baseline_metrics, model_metrics_dict):
        ax.axis('off')
        if not model_metrics_dict:
            return
        best_name = ''
        best_savings = -999
        best_pue = 999
        b_pwr = baseline_metrics['total_power_consumption']
        for k, v in model_metrics_dict.items():
            sav = (b_pwr - v['total_power_consumption']) / b_pwr * 100
            if sav > best_savings:
                best_savings = sav
                best_name = k
                best_pue = v.get('average_pue', 1.0)
        summary = f"\n        LEADERBOARD SUMMARY\n        ---------------------------\n        \n        TOP PERFORMER: {best_name.upper()}\n        \n        • Energy Savings: {best_savings:+.1f}%\n        • PUE Efficiency: {best_pue:.3f}\n        \n        MODELS TESTED: {len(model_metrics_dict)}\n        BASELINE PUE : {baseline_metrics.get('average_pue', 1.0):.3f}\n        \n        Note: Deep comparisons are\n        available in the adjacent charts.\n        "
        ax.text(0.5, 0.5, summary, transform=ax.transAxes, fontsize=10, ha='center', va='center', family='monospace', bbox=dict(boxstyle='round', facecolor=self.colors['scari'], alpha=0.1, edgecolor=self.colors['scari'], linewidth=1))

    def create_power_breakdown_chart(self, baseline_data, model_data_dict):
        pass