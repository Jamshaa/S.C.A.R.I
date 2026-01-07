#!/usr/bin/env python3
import os, sys, argparse
import logging
from pathlib import Path

# Fix path to include src/
sys.path.insert(0, str(Path(__file__).parent))

# Initialize logging for the main script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

import subprocess

def train_model(config='configs/default.yaml', timesteps=500000, device='auto'):
    print("\n" + "="*70)
    print("🚀 TRAINING S.C.A.R.I.")
    print("="*70)
    
    cmd = [
        sys.executable, "-m", "src.cli.train",
        "--config", config,
        "--timesteps", str(timesteps),
        "--device", device
    ]
    subprocess.run(cmd, check=True)

def evaluate_model(model='data/trained_models/scari_final.zip', steps=5000):
    print("\n" + "="*70)
    print("📊 EVALUATING S.C.A.R.I.")
    print("="*70)
    
    cmd = [
        sys.executable, "-m", "src.cli.evaluate",
        "--model", model,
        "--steps", str(steps)
    ]
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description='S.C.A.R.I. Integration Point')
    parser.add_argument('--train', action='store_true', help='Start training cycle')
    parser.add_argument('--evaluate', action='store_true', help='Start evaluation comparison')
    parser.add_argument('--both', action='store_true', help='Train then evaluate')
    parser.add_argument('--timesteps', type=int, default=500000, help='Total timesteps for PPO')
    parser.add_argument('--config', default='configs/default.yaml', help='YAML file for hyperparams/physics')
    parser.add_argument('--device', default='auto', help='Hardware device (cpu, cuda, auto)')
    parser.add_argument('--eval-steps', type=int, default=5000, help='Step count for evaluation session')
    parser.add_argument('--model', default='data/trained_models/scari_final.zip', help='Path to .zip model')
    
    args = parser.parse_args()
    
    # Ensure structure is sound (sanity check)
    for folder in ['data/trained_models', 'logs', 'outputs']:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    if not (args.train or args.evaluate or args.both):
        parser.print_help()
        return 0
    
    if args.train or args.both:
        try:
            train_model(args.config, args.timesteps, args.device)
        except Exception as e:
            logger.error(f"Training cycle failed: {e}")
            return 1
    
    if args.evaluate or args.both:
        try:
            evaluate_model(args.model, args.eval_steps)
        except Exception as e:
            logger.error(f"Evaluation cycle failed: {e}")
            return 1
    
    print("\n" + "="*70)
    print("✅ Pipeline execution successful!")
    print("="*70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
