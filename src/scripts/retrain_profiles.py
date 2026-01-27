# src/scripts/retrain_profiles.py
import subprocess
import os
import sys
from pathlib import Path

def run_retraining():
    base_dir = Path(__file__).parent.parent.parent
    venv_python = str(base_dir / "venv" / "Scripts" / "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"

    profiles = [
        {"name": "production_safe", "profile": "PRODUCTION_SAFE", "steps": 100000},
        {"name": "maximum_efficiency", "profile": "MAX_EFFICIENCY", "steps": 100000}
    ]

    print("🚀 SCARI-v2 Global Retraining Sequence Started...")
    
    for p in profiles:
        print(f"\n--- Training Profile: {p['profile']} ---")
        cmd = [
            venv_python, "train.py",
            "--profile", p['profile'],
            "--timesteps", str(p['steps']),
            "--model-dir", "data/models"
        ]
        
        # We'll rename the final model immediately after training
        try:
            subprocess.run(cmd, check=True)
            
            # Rename model to match profile expectations
            model_path = base_dir / "data" / "models" / "scari_v2_final.zip"
            target_path = base_dir / "data" / "models" / f"scari_{p['name']}.zip"
            
            if model_path.exists():
                if target_path.exists():
                    target_path.unlink()
                model_path.rename(target_path)
                print(f"✅ Saved profile model to {target_path}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Training failed for {p['profile']}: {e}")
            
    print("\n🎉 Global Retraining Sequence Complete!")

if __name__ == "__main__":
    run_retraining()
