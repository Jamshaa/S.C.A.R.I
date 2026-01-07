# src/cli/train.py
import click
import os
import logging
from pathlib import Path
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
import numpy as np
from src.config import Config

logger = logging.getLogger(__name__)

@click.command()
@click.option('--config', default='configs/default.yaml', help='Config file path')
@click.option('--timesteps', default=500000, type=int, help='Total training timesteps')
@click.option('--model-dir', default='data/trained_models', help='Model save directory')
@click.option('--log-dir', default='logs', help='Log directory')
@click.option('--device', default='auto', help='Device: cpu or cuda')
@click.option('--seed', default=42, type=int, help='Random seed')
def train(config: str, timesteps: int, model_dir: str, log_dir: str, device: str, seed: int) -> None:
    """Train S.C.A.R.I. agent using Proximal Policy Optimization (PPO)."""
    
    print("="*70)
    print("S.C.A.R.I. - Training Script")
    print("="*70)
    
    np.random.seed(seed)
    
    # Deferred import to avoid circular dependencies or heavy initialization if only using CLI help
    from src.envs.datacenter_env import DataCenterEnv
    
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Training started. Seed: {seed}, Device: {device}")
    
    print(f"\n📂 Directories created:")
    print(f"   Model dir: {model_dir}")
    print(f"   Log dir: {log_dir}")
    
    print(f"\n⚙️  Loading configuration from: {config}")
    try:
        cfg = Config.from_yaml(config)
    except Exception:
        print(f"⚠️  Config file not found or invalid at {config}. Using DEFAULT_CONFIG.")
        from src.config import DEFAULT_CONFIG
        cfg = DEFAULT_CONFIG
    
    print(f"   - Physics: ambient={cfg.physics.ambient_temp}ºC, max_temp={cfg.physics.max_temp}ºC")
    print(f"   - Training: timesteps={cfg.training.timesteps}, lr={cfg.training.learning_rate}")
    
    print(f"\n🌍 Creating and normalizing environment...")
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    
    def make_env():
        env = DataCenterEnv(cfg)
        env = Monitor(env, log_dir)
        return env
        
    env = DummyVecEnv([make_env])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    print(f"   - Observation space: {env.observation_space}")
    print(f"   - Action space: {env.action_space}")
    
    print(f"\n🤖 Initializing PPO agent...")
    from src.models.attention_policy import AttentionPolicy
    
    policy_kwargs = {
        'net_arch': [256, 256],
        'activation_fn': nn.ReLU,
    }
    
    # Selection of policy (Attention is now default for v10.0 realism)
    policy_type = 'Attention' 
    
    model = PPO(
        AttentionPolicy if policy_type == 'Attention' else 'MlpPolicy',
        env, verbose=1, tensorboard_log=log_dir,
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
        policy_kwargs=None if policy_type == 'Attention' else policy_kwargs,
        device=device,
        seed=seed,
    )
    
    print(f"   ✅ PPO agent created successfully")
    
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path=model_dir,
        name_prefix='scari',
        save_replay_buffer=True,
    )
    
    print(f"\n🚀 Starting training...")
    print(f"   Total timesteps: {timesteps:,}")
    print(f"   " + "="*66)
    
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=checkpoint_callback,
            tb_log_name='SCARI',
            log_interval=10,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    print(f"\n\n💾 Saving final model and stats...")
    model_path = os.path.join(model_dir, 'scari_final.zip')
    model.save(model_path)
    
    stats_path = os.path.join(model_dir, 'vec_normalize.pkl')
    env.save(stats_path)
    print(f"   ✅ Model saved: {model_path}")
    print(f"   ✅ Normalization stats saved: {stats_path}")
    
    config_path = os.path.join(model_dir, 'config.json')
    cfg.to_json(config_path)
    print(f"   ✅ Config saved: {config_path}")
    
    print(f"\n" + "="*70)
    print(f"✅ Training complete!")
    print(f"="*70)

if __name__ == '__main__':
    train()
