#!/usr/bin/env python3
"""
Quick example script to demonstrate improved S.C.A.R.I v11.0
This script runs a short training session and evaluation with the optimized configuration.
"""

import sys
import os
from pathlib import Path

def main():
    print("="*70)
    print("🚀 S.C.A.R.I v11.0 - Quick Demo")
    print("="*70)
    print("\nThis demo will:")
    print("1. Train a model for 10,000 steps (quick demo)")
    print("2. Evaluate against baseline")
    print("3. Generate visualizations")
    print("\n" + "="*70)
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Import after path setup
    from src.cli.train import train
    from src.cli.evaluate import evaluate
    import click
    
    # Quick training
    print("\n🧠 Starting quick training (10,000 steps)...")
    print("="*70)
    
    ctx = click.Context(train)
    ctx.invoke(
        train,
        config='configs/optimized.yaml',
        timesteps=10000,  # Quick demo
        model_dir='data/demo_models',
        log_dir='logs/demo',
        device='auto',
        seed=42
    )
    
    # Evaluation
    print("\n📊 Evaluating model...")
    print("="*70)
    
    ctx = click.Context(evaluate)
    ctx.invoke(
        evaluate,
        config='configs/optimized.yaml',
        model='data/demo_models/scari_v2_final.zip',
        steps=1000,  # Quick eval
        output='outputs/demo',
        seed=42
    )
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    print("\n📁 Check 'outputs/demo' for visualizations:")
    print("  - comprehensive_dashboard.png")
    print("  - power_breakdown.png")
    print("  - comparison.png")
    print("  - metrics.json")
    print("  - report.txt")
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
