# src/cli/train.py
import click
import os
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
import numpy as np
from src.config import Config
from src.envs.datacenter_env import DataCenterEnv

@click.command()
@click.option('--config', default='configs/default.yaml', help='Config file path')
@click.option('--timesteps', default=500000, type=int, help='Total training timesteps')
@click.option('--model-dir', default='data/trained_models', help='Model save directory')
@click.option('--log-dir', default='logs', help='Log directory')
@click.option('--device', default='auto', help='Device: cpu or cuda')
@click.option('--seed', default=42, type=int, help='Random seed')
def train(config, timesteps, model_dir, log_dir, device, seed):
    """Train S.C.A.R.I. agent using PPO"""
    
    print("="*70)
    print("S.C.A.R.I. v2.0 - Training Script")
    print("="*70)
    
    np.random.seed(seed)
    
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 Directories created:")
    print(f"   Model dir: {model_dir}")
    print(f"   Log dir: {log_dir}")
    
    print(f"\n⚙️  Loading configuration from: {config}")
    try:
        cfg = Config.from_yaml(config)
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {config}")
        print(f"   Using DEFAULT_CONFIG instead")
        from src.config import DEFAULT_CONFIG
        cfg = DEFAULT_CONFIG
    
    print(f"   - Physics: ambient={cfg.physics.ambient_temp}ºC, max_temp={cfg.physics.max_temp}ºC")
    print(f"   - Training: timesteps={cfg.training.timesteps}, lr={cfg.training.learning_rate}")
    print(f"   - Reward: energy_coeff={cfg.reward.energy_coefficient}, safe_threshold={cfg.reward.safe_threshold}ºC")
    
    print(f"\n🌍 Creating environment...")
    env = DataCenterEnv(cfg)
    env = Monitor(env, log_dir)
    print(f"   - Observation space: {env.observation_space}")
    print(f"   - Action space: {env.action_space}")
    print(f"   - Servers: {env.num_servers}")
    
    print(f"\n🤖 Initializing PPO agent...")
    
    policy_kwargs = {
        'net_arch': [256, 256],
        'activation_fn': 'relu',
    }
    
    model = PPO(
        'MlpPolicy', env, verbose=1, tensorboard_log=log_dir,
        learning_rate=cfg.training.learning_rate,
        n_steps=cfg.training.n_steps,
        batch_size=cfg.training.batch_size,
        gamma=cfg.training.gamma,
        gae_lambda=cfg.training.gae_lambda,
        ent_coef=cfg.training.ent_coef,
        vf_coef=cfg.training.vf_coef,
        max_grad_norm=cfg.training.max_grad_norm,
        n_epochs=cfg.training.n_epochs,
        clip_range=cfg.training.clip_range,
        policy_kwargs=policy_kwargs,
        device=device,
        seed=seed,
    )
    
    print(f"   ✅ PPO agent created successfully")
    print(f"   - Policy: MlpPolicy (256-256)")
    print(f"   - Device: {device}")
    
    print(f"\n📊 Setting up callbacks...")
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path=model_dir,
        name_prefix='scari',
        save_replay_buffer=True,
    )
    print(f"   ✅ Checkpoint callback created (save every 50k steps)")
    
    print(f"\n🚀 Starting training...")
    print(f"   Total timesteps: {timesteps:,}")
    print(f"   Expected duration: ~{timesteps/60000:.1f} minutes on GPU")
    print(f"   " + "="*66)
    
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=checkpoint_callback,
            tb_log_name='SCARI_v2',
            log_interval=10,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    
    print(f"\n\n💾 Saving final model...")
    model_path = os.path.join(model_dir, 'scari_v2_final.zip')
    model.save(model_path)
    print(f"   ✅ Model saved: {model_path}")
    
    config_path = os.path.join(model_dir, 'config.json')
    cfg.to_json(config_path)
    print(f"   ✅ Config saved: {config_path}")
    
    print(f"\n" + "="*70)
    print(f"✅ Training complete!")
    print(f"="*70)

if __name__ == '__main__':
    train()
