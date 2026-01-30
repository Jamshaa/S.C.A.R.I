# train.py
import argparse
import logging
from pathlib import Path
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import numpy as np

from src.utils.config import Config, DEFAULT_CONFIG
from src.envs.datacenter_env import DataCenterEnv
from src.models.policy import AttentionPolicy

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCARI")

def run_training():
    parser = argparse.ArgumentParser(description="SCARI: Advanced Datacenter Thermal Management")
    
    # Path handling
    # src/train.py -> parent is src, parent.parent is root
    base_dir = Path(__file__).parent.parent
    
    # Define paths
    default_config = base_dir / 'configs/default.yaml'
    default_models = base_dir / 'data/models'
    default_logs = base_dir / 'logs/tb'
    
    parser.add_argument('--config', type=str, default=str(default_config), help='Path to YAML config')
    parser.add_argument('--timesteps', type=int, help='Override total training timesteps')
    parser.add_argument('--model-dir', type=str, default=str(default_models), help='Save models here')
    parser.add_argument('--log-dir', type=str, default=str(default_logs), help='Tensorboard log directory')
    parser.add_argument('--device', type=str, default='auto', help='cpu or cuda')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--profile', type=str, default='BALANCED', choices=['BALANCED', 'PRODUCTION_SAFE', 'MAX_EFFICIENCY'], help='Reward profile')
    
    args = parser.parse_args()
    
    # Setup paths
    model_dir = Path(args.model_dir)
    log_dir = Path(args.log_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    np.random.seed(args.seed)
    
    print("="*70)
    print("🚀 SCARI: PRODUCTION TRAINING ENGINE")
    print("="*70)
    
    # Load configuration
    try:
        config_path = Path(args.config)
        cfg = Config.from_yaml(config_path) if config_path.exists() else DEFAULT_CONFIG
        if args.timesteps:
            cfg.training.timesteps = args.timesteps
        if args.profile:
            cfg.reward.profile = args.profile
    except Exception as e:
        logger.error(f"Failed to load config: {e}. Falling back to default.")
        cfg = DEFAULT_CONFIG
        cfg.reward.profile = args.profile # Ensure profile is set even if config fails

    print(f"\n📂 Environment Setup:")
    print(f"   - Config: {args.config}")
    print(f"   - Models: {model_dir}")
    print(f"   - Logs:   {log_dir}")
    print(f"   - Profile: {cfg.reward.profile}")
    
    # Environment creation
    def make_env():
        env = DataCenterEnv(cfg)
        env = Monitor(env, str(log_dir))
        return env
        
    env = DummyVecEnv([make_env])
    # VecNormalize is now handled internally in Env or here for scaling
    # We'll use SB3 normalization for rewards, but OBS normalization will be internal to the env for transparency
    env = VecNormalize(env, norm_obs=False, norm_reward=True, clip_obs=10.)
    
    print(f"\n🤖 Agent Configuration:")
    print(f"   - Policy: Attention (Thermal-Aware)")
    print(f"   - Device: {args.device}")
    
    model = PPO(
        AttentionPolicy,
        env,
        verbose=1,
        tensorboard_log=str(log_dir),
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
        device=args.device,
        seed=args.seed,
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=max(1000, cfg.training.timesteps // 10),
        save_path=str(model_dir),
        name_prefix='scari'
    )
    
    print(f"\n🚀 Training started for {cfg.training.timesteps:,} steps...")
    try:
        model.learn(
            total_timesteps=cfg.training.timesteps,
            callback=checkpoint_callback,
            tb_log_name='PPO_Production'
        )
        print("\n✅ Training complete!")
        # Save final model heavily distinct from emergency saves
        model.save(model_dir / "scari_final")
        
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted manually.")
        model.save(model_dir / "scari_crash_dump")
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
        
    except Exception as e:
        logger.error(f"Training crashed: {e}", exc_info=True)
        model.save(model_dir / "scari_crash_dump")
        print(f"\n🔥 CRITICAL ERROR: {e}")
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
        raise e
        
    finally:
        # Always save env stats
        try:
            env.save(model_dir / "vec_normalize.pkl")
            cfg.to_json(model_dir / "config.json")
            print(f"📝 Config and Env stats saved to {model_dir}")
        except Exception as e:
            logger.error(f"Failed to save final artifacts: {e}")


if __name__ == "__main__":
    run_training()
