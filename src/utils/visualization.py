# src/utils/visualization.py
"""
Advanced visualization module for S.C.A.R.I performance analysis.
Creates professional, publication-ready plots and dashboards.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Any
import seaborn as sns

# Set professional style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 10


class PerformanceVisualizer:
    """Creates comprehensive performance comparison visualizations."""
    
    def __init__(self, output_dir: str = "outputs"):
        """Initialize visualizer with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme
        self.colors = {
            'baseline': '#E63946',  # Sharp red - classic/legacy
            'scari': '#1D3557',     # Deep blue - professional AI
            'savings': '#A8DADC',   # High-contrast light teal
            'warning': '#FFB703',   # Amber warning
            'danger': '#D00000',    # Critical red
            'safe': '#2A9D8F',      # Professional green
            'background': '#F8F9FA' # Off-white background
        }
    
    def create_comprehensive_dashboard(
        self,
        baseline_metrics: Dict[str, Any],
        model_metrics: Dict[str, Any],
        baseline_data: Dict[str, List[float]],
        model_data: Dict[str, List[float]],
        save_individual: bool = True
    ) -> None:
        """
        Create a comprehensive performance dashboard and optionally individual charts.
        """
        # 1. First, generate individual high-res charts with clear titles
        if save_individual:
            self._save_individual_charts(baseline_metrics, model_metrics, baseline_data, model_data)

        # 2. Generate the summary dashboard
        fig = plt.figure(figsize=(20, 12))
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # ... (rest of the dashboard logic remains but we use the shared plotting methods)
        self._plot_power_comparison(fig.add_subplot(gs[0:2, 0]), baseline_data, model_data)
        self._plot_temperature_comparison(fig.add_subplot(gs[0:2, 1]), baseline_data, model_data)
        self._plot_cumulative_savings(fig.add_subplot(gs[0:2, 2]), baseline_data, model_data)
        self._plot_pue_comparison(fig.add_subplot(gs[2, 0]), baseline_metrics, model_metrics)
        self._plot_efficiency_metrics(fig.add_subplot(gs[2, 1]), baseline_metrics, model_metrics)
        self._plot_summary_card(fig.add_subplot(gs[2, 2]), baseline_metrics, model_metrics)
        
        # Main title
        savings_pct = ((baseline_metrics['total_power_consumption'] - 
                       model_metrics['total_power_consumption']) / 
                       baseline_metrics['total_power_consumption'] * 100)
        
        title_color = self.colors['safe'] if savings_pct > 0 else self.colors['danger']
        fig.suptitle(
            f'SCARI Performance Report | Total Savings: {savings_pct:.1f}%',
            fontsize=22, fontweight='bold', color=title_color
        )
        
        plt.savefig(self.output_dir / 'comprehensive_dashboard.png', 
                   bbox_inches='tight', facecolor='white', dpi=300)
        plt.close()

    def _save_individual_charts(self, bm, mm, bd, md):
        """Saves each metric as a standalone, clear image."""
        plots = [
            (self._plot_power_comparison, (bd, md), '1_electricity_usage.png'),
            (self._plot_temperature_comparison, (bd, md), '2_thermal_safety.png'),
            (self._plot_cumulative_savings, (bd, md), '3_total_savings.png'),
            (self._plot_pue_comparison, (bm, mm), '4_efficiency_score.png'),
        ]
        
        for func, args, filename in plots:
            fig, ax = plt.subplots(figsize=(10, 6))
            func(ax, *args)
            plt.savefig(self.output_dir / filename, bbox_inches='tight', dpi=300)
            plt.close()
    
    def _plot_power_comparison(self, ax, baseline_data, model_data):
        """Plot detailed power consumption comparison."""
        time = np.arange(len(baseline_data['powers']))
        
        # Plot both lines
        ax.plot(time, baseline_data['powers'], 
               label='Baseline Controller', color=self.colors['baseline'],
               linewidth=2, alpha=0.8)
        ax.plot(time, model_data['powers'], 
               label='S.C.A.R.I Agent', color=self.colors['scari'],
               linewidth=2, alpha=0.8)
        
        # Highlight savings regions
        savings_mask = np.array(model_data['powers']) < np.array(baseline_data['powers'])
        if savings_mask.any():
            ax.fill_between(time, baseline_data['powers'], model_data['powers'],
                           where=savings_mask, color=self.colors['savings'],
                           alpha=0.3, label='Energy Saved')
        
        ax.set_xlabel('Time Steps (Simulation)', fontweight='regular')
        ax.set_ylabel('Electricity Consumption (Watts)', fontweight='bold')
        ax.set_title('Electricity Usage: SCARI vs Standard', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Add average lines
        baseline_avg = np.mean(baseline_data['powers'])
        model_avg = np.mean(model_data['powers'])
        
        # Annotations (Clearer for beginners)
        ax.text(0.02, 0.98, f'Standard System: {baseline_avg:.0f}W (Average)',
               transform=ax.transAxes, va='top', fontsize=9,
               bbox=dict(boxstyle='round', facecolor=self.colors['baseline'], alpha=0.2))
        ax.text(0.02, 0.92, f'SCARI AI System: {model_avg:.0f}W (Average)',
               transform=ax.transAxes, va='top', fontsize=9,
               bbox=dict(boxstyle='round', facecolor=self.colors['scari'], alpha=0.2))
    
    def _plot_temperature_comparison(self, ax, baseline_data, model_data):
        """Plot temperature management strategies."""
        time = np.arange(len(baseline_data['temps']))
        
        # Plot temperatures
        ax.plot(time, baseline_data['temps'],
               label='Baseline', color=self.colors['baseline'],
               linewidth=2, alpha=0.8)
        ax.plot(time, model_data['temps'],
               label='S.C.A.R.I', color=self.colors['scari'],
               linewidth=2, alpha=0.8)
        
        # Add safe operating zones
        ax.axhspan(0, 70, alpha=0.1, color=self.colors['safe'], label='Optimal Zone')
        ax.axhspan(70, 85, alpha=0.1, color=self.colors['warning'], label='Caution Zone')
        ax.axhspan(85, 100, alpha=0.1, color=self.colors['danger'], label='Danger Zone')
        
        ax.set_xlabel('Time Steps (Simulation)', fontweight='regular')
        ax.set_ylabel('Server Temperature (°C)', fontweight='bold')
        ax.set_title('Thermal Safety: Keeping Servers Cool', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', framealpha=0.9, fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(40, 95)
        
        # Statistics annotations
        baseline_avg_temp = np.mean(baseline_data['temps'])
        model_avg_temp = np.mean(model_data['temps'])
        ax.text(0.02, 0.98, 
               f'Baseline: μ={baseline_avg_temp:.1f}°C, σ={np.std(baseline_data["temps"]):.1f}°C',
               transform=ax.transAxes, va='top', fontsize=8,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax.text(0.02, 0.91,
               f'SCARI: μ={model_avg_temp:.1f}°C, σ={np.std(model_data["temps"]):.1f}°C',
               transform=ax.transAxes, va='top', fontsize=8,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def _plot_cumulative_savings(self, ax, baseline_data, model_data):
        """Plot cumulative energy savings over time."""
        baseline_cumsum = np.cumsum(baseline_data['powers']) / 1000.0  # Convert to kW
        model_cumsum = np.cumsum(model_data['powers']) / 1000.0
        savings_cumsum = baseline_cumsum - model_cumsum
        
        time = np.arange(len(savings_cumsum))
        
        # Plot cumulative savings
        color = self.colors['safe'] if savings_cumsum[-1] > 0 else self.colors['danger']
        ax.plot(time, savings_cumsum, color=color, linewidth=3)
        ax.fill_between(time, 0, savings_cumsum, alpha=0.3, color=color)
        
        ax.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)
        ax.set_xlabel('Time Steps (Simulation)', fontweight='regular')
        ax.set_ylabel('Total Energy Saved (kWh)', fontweight='bold')
        ax.set_title('Money Saved: Cumulative Progress', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Final savings annotation
        final_savings = savings_cumsum[-1]
        savings_pct = (final_savings / baseline_cumsum[-1]) * 100 if baseline_cumsum[-1] > 0 else 0
        
        ax.text(0.98, 0.98,
               f'Total Saved: {final_savings:+.2f} kWh\n({savings_pct:+.1f}%)',
               transform=ax.transAxes, ha='right', va='top',
               fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
    
    def _plot_pue_comparison(self, ax, baseline_metrics, model_metrics):
        """Bar chart comparing PUE values."""
        categories = ['Baseline', 'S.C.A.R.I']
        pue_values = [
            baseline_metrics.get('average_pue', 1.0),
            model_metrics.get('average_pue', 1.0)
        ]
        
        colors = [self.colors['baseline'], self.colors['scari']]
        bars = ax.bar(categories, pue_values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        
        # Add reference line for ideal PUE
        ax.axhline(1.0, color='green', linestyle='--', linewidth=2, 
                  label='Ideal PUE = 1.0', alpha=0.7)
        ax.axhline(1.2, color='orange', linestyle='--', linewidth=1.5,
                  label='Industry Target = 1.2', alpha=0.7)
        
        ax.set_ylabel('Efficiency Score (PUE)', fontweight='bold')
        ax.set_title('How Efficient is the Cooling? (Lower is better)', fontsize=12, fontweight='bold')
        ax.legend(fontsize=8)
        # Zoom in on the important range for PUE
        ax.set_ylim(1.0, max(pue_values) * 1.1)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, pue_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.3f}',
                   ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    def _plot_efficiency_metrics(self, ax, baseline_metrics, model_metrics):
        """Horizontal bar chart showing multiple efficiency dimensions."""
        categories = ['Energy\nEfficiency', 'Thermal\nStability', 
                     'System\nHealth', 'PUE\nScore']
        
        # Normalize metrics to 0-100 scale
        baseline_scores = [
            (1.0 - min(1.0, baseline_metrics.get('total_power_consumption', 20e6) / 25e6)) * 100,
            baseline_metrics.get('thermal_stability', 0.95) * 100,
            baseline_metrics.get('average_health', 0.99) * 100,
            max(0, (1.5 - baseline_metrics.get('average_pue', 1.015))) * 100
        ]
        
        model_scores = [
            (1.0 - min(1.0, model_metrics.get('total_power_consumption', 20e6) / 25e6)) * 100,
            model_metrics.get('thermal_stability', 0.95) * 100,
            model_metrics.get('average_health', 0.99) * 100,
            max(0, (1.5 - model_metrics.get('average_pue', 1.015))) * 100
        ]
        
        y_pos = np.arange(len(categories))
        bar_height = 0.35
        
        # Create horizontal bars
        ax.barh(y_pos - bar_height/2, baseline_scores, bar_height,
               label='Baseline', color=self.colors['baseline'], alpha=0.7)
        ax.barh(y_pos + bar_height/2, model_scores, bar_height,
               label='S.C.A.R.I', color=self.colors['scari'], alpha=0.7)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=9)
        ax.set_xlabel('Score (%)', fontweight='bold')
        ax.set_xlim(0, 100)
        ax.set_title('Multi-Dimensional Performance', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (b_score, m_score) in enumerate(zip(baseline_scores, model_scores)):
            ax.text(b_score + 1, i - bar_height/2, f'{b_score:.0f}', 
                   va='center', fontsize=7)
            ax.text(m_score + 1, i + bar_height/2, f'{m_score:.0f}',
                   va='center', fontsize=7)
    
    def _plot_summary_card(self, ax, baseline_metrics, model_metrics):
        """Text summary card with key metrics."""
        ax.axis('off')
        
        # Calculate key differences
        power_diff = baseline_metrics['total_power_consumption'] - model_metrics['total_power_consumption']
        power_pct = (power_diff / baseline_metrics['total_power_consumption']) * 100
        
        pue_diff = baseline_metrics.get('average_pue', 1.0) - model_metrics.get('average_pue', 1.0)
        
        temp_diff = model_metrics['average_temperature'] - baseline_metrics['average_temperature']
        
        # Create summary text
        if power_pct > 0:
            verdict = "PERFORMANCE IMPROVED"
            verdict_color = self.colors['safe']
        elif power_pct > -2:
            verdict = "MARGINAL PERFORMANCE"
            verdict_color = self.colors['warning']
        else:
            verdict = "PERFORMANCE REGRESSION"
            verdict_color = self.colors['danger']
        
        summary = f"""
        {verdict}
        ---------------------------
        
        ENERGY SAVINGS
        • Power Efficiency: {power_pct:+.1f}%
        • Total Energy Δ: {power_diff/1e6:+.2f} MWh
        
        COOLING EFFICIENCY
        • PUE Improvement: {pue_diff:+.3f}
        • Final SCARI PUE: {model_metrics.get('average_pue', 1.0):.3f}
        
        THERMAL CONTROL
        • Mean Temp Δ: {temp_diff:+.1f}°C
        • Max Observed: {model_metrics['max_temperature']:.1f}°C
        
        SAFETY & RELIABILITY
        • Safety Violations: {model_metrics.get('safety_violations', 0)}
        • Average Health: {model_metrics.get('average_health', 1.0):.4f}
        """
        
        ax.text(0.5, 0.5, summary, transform=ax.transAxes,
               fontsize=9, ha='center', va='center', family='monospace',
               bbox=dict(boxstyle='round', facecolor=verdict_color, 
                        alpha=0.2, edgecolor=verdict_color, linewidth=2))
    
    def create_power_breakdown_chart(self, baseline_data, model_data):
        """Create stacked area chart showing IT vs Cooling power."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        time = np.arange(len(baseline_data['it_powers']))
        
        # Baseline breakdown
        ax1.fill_between(time, 0, baseline_data['it_powers'],
                        label='IT Power', color='#FF9999', alpha=0.7)
        ax1.fill_between(time, baseline_data['it_powers'],
                        np.array(baseline_data['it_powers']) + np.array(baseline_data['cooling_powers']),
                        label='Cooling Power', color='#66B2FF', alpha=0.7)
        ax1.set_xlabel('Time Steps', fontweight='bold')
        ax1.set_ylabel('Power (W)', fontweight='bold')
        ax1.set_title('Baseline Power Breakdown', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # SCARI breakdown
        ax2.fill_between(time, 0, model_data['it_powers'],
                        label='IT Power', color='#FF9999', alpha=0.7)
        ax2.fill_between(time, model_data['it_powers'],
                        np.array(model_data['it_powers']) + np.array(model_data['cooling_powers']),
                        label='Cooling Power', color='#66B2FF', alpha=0.7)
        ax2.set_xlabel('Time Steps', fontweight='bold')
        ax2.set_ylabel('Power (W)', fontweight='bold')
        ax2.set_title('S.C.A.R.I Power Breakdown', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'power_breakdown.png', bbox_inches='tight', dpi=300)
        plt.close()
        print(f"Power breakdown chart saved to {self.output_dir / 'power_breakdown.png'}")
