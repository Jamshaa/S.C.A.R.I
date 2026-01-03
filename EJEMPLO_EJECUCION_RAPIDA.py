#!/usr/bin/env python3
"""
S.C.A.R.I. v2.0 - Fast Execution Demo
A quick script to verify the physics and environment without full training.
"""

import numpy as np
from pathlib import Path
import sys
import logging

# Ensure src/ is in path
sys.path.insert(0, str(Path(__file__).parent))

# Quiet down some logs during demo
logging.basicConfig(level=logging.WARNING)

def main():
    print("="*70)
    print("S.C.A.R.I. v2.0 - Fast Execution Example (Verified)")
    print("="*70)
    
    try:
        print("\n1️⃣  Loading Physics Configuration...")
        from src.config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
        print(f"   ✅ Config validated: {config.physics.p_max}W max IT power")
        
        print("\n2️⃣  Constructing RL Environment...")
        from src.envs.datacenter_env import DataCenterEnv
        env = DataCenterEnv(config)
        print(f"   ✅ Space detected: Obs={env.observation_space.shape}, Action={env.action_space.shape}")
        
        print("\n3️⃣  Running Baseline (Random Policy)...")
        obs, _ = env.reset()
        random_rewards = []
        for step in range(10):
            action = env.action_space.sample()
            obs, reward, term, trunc, info = env.step(action)
            random_rewards.append(reward)
            if step % 3 == 0:
                print(f"   Step {step+1:2d}: Rack Power={info['total_power']:6.0f}W | T_max={info['max_temp']:5.1f}ºC")
        
        print("\n4️⃣  Running Simple Heuristic (Manual PID)...")
        class SimpleHeuristic:
            def get_action(self, temps, n):
                # Aggressive cooling if T > 50C
                target = 50.0
                error = np.max(temps) - target
                speed = np.clip(0.2 + 0.05 * error, 0.1, 1.0)
                return np.ones(n) * speed
        
        obs, _ = env.reset()
        heuristic = SimpleHeuristic()
        heuristic_rewards = []
        for step in range(10):
            temps = obs[:env.num_servers]
            action = heuristic.get_action(temps, env.num_servers)
            obs, reward, term, trunc, info = env.step(action)
            heuristic_rewards.append(reward)
        
        print("\n5️⃣  Quick Comparison (Heuristic vs Random)...")
        improvement = np.mean(heuristic_rewards) - np.mean(random_rewards)
        print(f"   Heuristic Avg Reward: {np.mean(heuristic_rewards):>8.2f}")
        print(f"   Random Avg Reward:    {np.mean(random_rewards):>8.2f}")
        print(f"   Net Gain:             {improvement:>+8.2f}")
        
        print("\n" + "="*70)
        print("✅ Demo completed successfully!")
        print("="*70)
        print("\n🚀 Next command to try:")
        print("   python main.py --train --timesteps 50000")
        
    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
