import argparse
import logging
from pathlib import Path
import re
import sys
from typing import Callable
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import numpy as np
from src.utils.config import Config, DEFAULT_CONFIG, COOLING_COST_DB, PREFERRED_CONFIG_PATH, get_available_config_paths, prompt_for_config_selection, resolve_config_file
from src.envs.datacenter_env import DataCenterEnv
from src.models.policy import AttentionPolicy
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SCARI')
OUTPUT_NAME_PATTERN = re.compile(r'[^A-Za-z0-9._ -]+')


def normalize_output_name(value: str) -> str:
    cleaned = OUTPUT_NAME_PATTERN.sub('', (value or '').strip()).replace(' ', '_')
    cleaned = cleaned.strip('._-')
    if not cleaned:
        raise ValueError('output name must contain letters or numbers')
    return cleaned[:80]


def choose_config_path(config_argument: str | None) -> Path:
    if config_argument:
        return resolve_config_file(config_argument)
    if sys.stdin.isatty() and sys.stdout.isatty():
        print(f'\nNo --config specified. Press Enter to use {PREFERRED_CONFIG_PATH.name} or choose another profile.')
        return prompt_for_config_selection(PREFERRED_CONFIG_PATH)
    return resolve_config_file(PREFERRED_CONFIG_PATH)


def print_available_configs() -> None:
    for config_path in get_available_config_paths():
        marker = ' (default)' if config_path.resolve() == PREFERRED_CONFIG_PATH.resolve() else ''
        print(f'- {config_path.name}{marker}')


def apply_training_overrides(cfg: Config, args: argparse.Namespace) -> Config:
    if args.timesteps:
        cfg.training.timesteps = args.timesteps
    if getattr(args, 'profile', None):
        cfg.reward.profile = args.profile
    cfg.cooling.mode = args.cooling_mode.upper()
    if cfg.cooling.mode in COOLING_COST_DB:
        db = COOLING_COST_DB[cfg.cooling.mode]
        cfg.cooling.capex_per_server = db['capex_per_server_eur']
        cfg.cooling.opex_per_server_year = db['opex_per_server_year_eur']
    return cfg


def build_learning_rate(training_cfg) -> float | Callable[[float], float]:
    base_lr = float(training_cfg.learning_rate)
    if not training_cfg.use_linear_lr_schedule:
        return base_lr
    end_factor = float(np.clip(training_cfg.learning_rate_end_factor, 0.01, 1.0))
    end_lr = max(base_lr * end_factor, 1e-8)

    def schedule(progress_remaining: float) -> float:
        return end_lr + (base_lr - end_lr) * float(progress_remaining)

    return schedule

def run_training():
    parser = argparse.ArgumentParser(description='S.C.A.R.I: Advanced Datacenter Thermal Management Training')
    base_dir = Path(__file__).parent.parent
    default_models = base_dir / 'data/models'
    default_logs = base_dir / 'logs/tb'
    parser.add_argument('--config', type=str, help='Config path; if omitted, default.yaml is used by default')
    parser.add_argument('--list-configs', action='store_true', help='List available YAML configs and exit')
    parser.add_argument('--timesteps', type=int, help='Override total training timesteps')
    parser.add_argument('--model-dir', type=str, default=str(default_models))
    parser.add_argument('--log-dir', type=str, default=str(default_logs))
    parser.add_argument('--device', type=str, default='auto')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--profile', type=str, help='Optional metadata label for the run; does not change reward logic')
    parser.add_argument('--output-name', type=str, default='scari_final')
    parser.add_argument('--cooling-mode', type=str, default='AIR', choices=['AIR', 'LIQUID', 'HYBRID'], help='Cooling system type: AIR, LIQUID, or HYBRID')
    args = parser.parse_args()
    if args.list_configs:
        print_available_configs()
        return
    args.output_name = normalize_output_name(args.output_name)
    model_dir = Path(args.model_dir)
    log_dir = Path(args.log_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    np.random.seed(args.seed)
    saved_model_name = None
    print('=' * 70)
    print('🚀 S.C.A.R.I — PRODUCTION TRAINING ENGINE')
    print('=' * 70)
    config_path = choose_config_path(args.config)
    try:
        cfg = Config.from_yaml(config_path)
    except Exception as e:
        logger.error(f'Failed to load config: {e}. Falling back to optimized profile.')
        try:
            config_path = resolve_config_file(PREFERRED_CONFIG_PATH)
            cfg = Config.from_yaml(config_path)
        except Exception:
            cfg = DEFAULT_CONFIG
    cfg = apply_training_overrides(cfg, args)
    num_servers = cfg.environment.num_racks * cfg.environment.servers_per_rack
    cost_summary = cfg.cooling.get_cost_summary(num_servers)
    print(f'\n📂 Configuration:')
    print(f'   Config file : {config_path}')
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
    env = VecNormalize(env, norm_obs=cfg.training.normalize_observation, norm_reward=True, clip_obs=10.0)
    print(f'\n🤖 Agent:')
    print(f'   Policy : Attention (Thermal-Aware)')
    print(f'   Device : {args.device}')
    print(f'   Steps  : {cfg.training.timesteps:,}')
    model = PPO(AttentionPolicy, env, verbose=1, tensorboard_log=str(log_dir), learning_rate=build_learning_rate(cfg.training), n_steps=cfg.training.n_steps, batch_size=cfg.training.batch_size, gamma=cfg.training.gamma, gae_lambda=cfg.training.gae_lambda, normalize_advantage=cfg.training.normalize_advantage, ent_coef=cfg.training.ent_coef, vf_coef=cfg.training.vf_coef, max_grad_norm=cfg.training.max_grad_norm, n_epochs=cfg.training.n_epochs, clip_range=cfg.training.clip_range, device=args.device, seed=args.seed)
    checkpoint_callback = CheckpointCallback(save_freq=max(1000, cfg.training.timesteps // 10), save_path=str(model_dir), name_prefix='scari')
    print(f'\n🚀 Training started for {cfg.training.timesteps:,} steps...')
    try:
        model.learn(total_timesteps=cfg.training.timesteps, callback=checkpoint_callback, tb_log_name='PPO_Production')
        print('\n✅ Training complete!')
        model.save(model_dir / args.output_name)
        saved_model_name = args.output_name
    except KeyboardInterrupt:
        print('\n⚠️  Training interrupted manually.')
        model.save(model_dir / 'scari_crash_dump')
        saved_model_name = 'scari_crash_dump'
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
    except Exception as e:
        logger.error(f'Training crashed: {e}', exc_info=True)
        model.save(model_dir / 'scari_crash_dump')
        saved_model_name = 'scari_crash_dump'
        print(f'\n🔥 CRITICAL ERROR: {e}')
        print(f"💾 Crash dump saved to {model_dir / 'scari_crash_dump'}")
        raise e
    finally:
        try:
            model_dir.mkdir(parents=True, exist_ok=True)
            if 'env' in locals() and hasattr(env, 'save'):
                env.save(model_dir / 'vec_normalize.pkl')
                if saved_model_name:
                    env.save(model_dir / f'{Path(saved_model_name).stem}_vec_normalize.pkl')
            cfg.to_json(model_dir / 'config.json')
            print(f'📝 Config saved to {model_dir}')
            if 'env' in locals():
                env.close()
        except Exception as e:
            logger.error(f'Failed to save final artifacts: {e}')
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
if __name__ == '__main__':
    run_training()
    import sys
    sys.exit(0)
