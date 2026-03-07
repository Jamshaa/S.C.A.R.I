import argparse
import logging
from pathlib import Path
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import numpy as np
from src.utils.config import Config, DEFAULT_CONFIG, COOLING_COST_DB
from src.envs.datacenter_env import DataCenterEnv
from src.models.policy import AttentionPolicy
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SCARI')

def run_training():
    parser = argparse.ArgumentParser(description='S.C.A.R.I: Advanced Datacenter Thermal Management Training')
    base_dir = Path(__file__).parent.parent
    default_config = base_dir / 'configs/default.yaml'
    default_models = base_dir / 'data/models'
    default_logs = base_dir / 'logs/tb'
    parser.add_argument('--config', type=str, default=str(default_config))
    parser.add_argument('--timesteps', type=int, help='Override total training timesteps')
    parser.add_argument('--model-dir', type=str, default=str(default_models))
    parser.add_argument('--log-dir', type=str, default=str(default_logs))
    parser.add_argument('--device', type=str, default='auto')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--profile', type=str, default='ENERGY_FIRST', choices=['ENERGY_FIRST', 'BALANCED', 'PRODUCTION_SAFE'])
    parser.add_argument('--output-name', type=str, default='scari_final')
    parser.add_argument('--cooling-mode', type=str, default='AIR', choices=['AIR', 'LIQUID', 'HYBRID'], help='Cooling system type: AIR, LIQUID, or HYBRID')
    args = parser.parse_args()
    model_dir = Path(args.model_dir)
    log_dir = Path(args.log_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    np.random.seed(args.seed)
    print('=' * 70)
    print('🚀 S.C.A.R.I — PRODUCTION TRAINING ENGINE')
    print('=' * 70)
    try:
        config_path = Path(args.config)
        cfg = Config.from_yaml(config_path) if config_path.exists() else DEFAULT_CONFIG
    except Exception as e:
        logger.error(f'Failed to load config: {e}. Falling back to default.')
        cfg = DEFAULT_CONFIG
    if args.timesteps:
        cfg.training.timesteps = args.timesteps
    if args.profile:
        cfg.reward.profile = args.profile
    cfg.cooling.mode = args.cooling_mode.upper()
    if cfg.cooling.mode in COOLING_COST_DB:
        db = COOLING_COST_DB[cfg.cooling.mode]
        cfg.cooling.capex_per_server = db['capex_per_server_eur']
        cfg.cooling.opex_per_server_year = db['opex_per_server_year_eur']
    num_servers = cfg.environment.num_racks * cfg.environment.servers_per_rack
    cost_summary = cfg.cooling.get_cost_summary(num_servers)
    print(f'\n📂 Configuration:')
    print(f'   Config file : {args.config}')
    print(f'   Models dir  : {model_dir}')
    print(f'   Logs dir    : {log_dir}')
    print(f'   Profile     : {cfg.reward.profile}')
    print(f'\n❄️  Cooling System:')
    print(f'   Mode        : {cfg.cooling.mode}')
    print(f"   CAPEX total : €{cost_summary['capex_total_eur']:,.0f}")
    print(f"   OPEX/year   : €{cost_summary['opex_annual_eur']:,.0f}")
    print(f"   TCO (5yr)   : €{cost_summary['tco_eur']:,.0f}")

    def make_env():
        env = DataCenterEnv(cfg)
        env = Monitor(env, str(log_dir))
        return env
    env = DummyVecEnv([make_env])
    env = VecNormalize(env, norm_obs=False, norm_reward=True, clip_obs=10.0)
    print(f'\n🤖 Agent:')
    print(f'   Policy : Attention (Thermal-Aware)')
    print(f'   Device : {args.device}')
    print(f'   Steps  : {cfg.training.timesteps:,}')
    model = PPO(AttentionPolicy, env, verbose=1, tensorboard_log=str(log_dir), learning_rate=cfg.training.learning_rate, n_steps=cfg.training.n_steps, batch_size=cfg.training.batch_size, gamma=cfg.training.gamma, gae_lambda=cfg.training.gae_lambda, ent_coef=cfg.training.ent_coef, vf_coef=cfg.training.vf_coef, max_grad_norm=cfg.training.max_grad_norm, n_epochs=cfg.training.n_epochs, clip_range=cfg.training.clip_range, device=args.device, seed=args.seed)
    checkpoint_callback = CheckpointCallback(save_freq=max(1000, cfg.training.timesteps // 10), save_path=str(model_dir), name_prefix='scari')
    print(f'\n🚀 Training started for {cfg.training.timesteps:,} steps...')
    try:
        model.learn(total_timesteps=cfg.training.timesteps, callback=checkpoint_callback, tb_log_name='PPO_Production')
        print('\n✅ Training complete!')
        model.save(model_dir / args.output_name)
    except KeyboardInterrupt:
        print('\n⚠️  Training interrupted manually.')
        model.save(model_dir / 'scari_crash_dump')
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
    except Exception as e:
        logger.error(f'Training crashed: {e}', exc_info=True)
        model.save(model_dir / 'scari_crash_dump')
        print(f'\n🔥 CRITICAL ERROR: {e}')
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
        raise e
    finally:
        try:
            if 'env' in locals():
                env.close()
            model_dir.mkdir(parents=True, exist_ok=True)
            if 'env' in locals() and hasattr(env, 'save'):
                env.save(model_dir / 'vec_normalize.pkl')
            cfg.to_json(model_dir / 'config.json')
            print(f'📝 Config saved to {model_dir}')
        except Exception as e:
            logger.error(f'Failed to save final artifacts: {e}')
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
if __name__ == '__main__':
    run_training()
    import sys
    sys.exit(0)