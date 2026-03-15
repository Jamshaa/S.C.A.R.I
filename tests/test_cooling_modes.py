import pytest
import numpy as np
from src.utils.config import Config, CoolingConfig, COOLING_COST_DB, DEFAULT_CONFIG
from src.models.cooling import CoolingSystem
from src.models.server import Server
from src.envs.datacenter_env import DataCenterEnv

class TestCoolingCostDatabase:

    def test_all_modes_present(self):
        assert 'AIR' in COOLING_COST_DB
        assert 'LIQUID' in COOLING_COST_DB
        assert 'HYBRID' in COOLING_COST_DB

    def test_cost_fields_present(self):
        for mode, data in COOLING_COST_DB.items():
            assert 'capex_per_server_eur' in data, f'{mode} missing capex'
            assert 'opex_per_server_year_eur' in data, f'{mode} missing opex'
            assert 'typical_pue' in data, f'{mode} missing PUE'
            assert 'label' in data, f'{mode} missing label'

    def test_liquid_more_expensive_than_air(self):
        air = COOLING_COST_DB['AIR']
        liquid = COOLING_COST_DB['LIQUID']
        assert liquid['capex_per_server_eur'] > air['capex_per_server_eur']

    def test_liquid_better_pue_than_air(self):
        air = COOLING_COST_DB['AIR']
        liquid = COOLING_COST_DB['LIQUID']
        assert liquid['typical_pue'] < air['typical_pue']

class TestCoolingConfig:

    def test_cost_summary_air(self):
        cfg = CoolingConfig(mode='AIR')
        summary = cfg.get_cost_summary(num_servers=100, years=5)
        assert summary['mode'] == 'AIR'
        assert summary['num_servers'] == 100
        assert summary['capex_total_eur'] > 0
        assert summary['opex_annual_eur'] > 0
        assert summary['tco_eur'] == summary['capex_total_eur'] + summary['opex_annual_eur'] * 5

    def test_cost_summary_liquid(self):
        cfg = CoolingConfig(mode='LIQUID')
        summary = cfg.get_cost_summary(num_servers=50)
        assert summary['mode'] == 'LIQUID'
        assert summary['capex_per_server_eur'] == COOLING_COST_DB['LIQUID']['capex_per_server_eur']

    def test_cost_summary_hybrid(self):
        cfg = CoolingConfig(mode='HYBRID')
        summary = cfg.get_cost_summary(num_servers=10, years=10)
        assert summary['tco_years'] == 10

class TestCoolingSystem:

    @pytest.fixture(params=['AIR', 'LIQUID', 'HYBRID'])
    def cooling(self, request):
        return CoolingSystem(mode=request.param)

    def test_initialization(self, cooling):
        assert cooling.mode in ('AIR', 'LIQUID', 'HYBRID')
        assert cooling.efficiency_factor == 1.0

    def test_zero_flow_power(self, cooling):
        power = cooling.get_power_consumption(0.0)
        assert power >= 0.0
        assert power < 50.0

    def test_max_flow_power(self, cooling):
        power = cooling.get_power_consumption(1.0)
        assert power > 0.0

    def test_cooling_capacity_positive(self, cooling):
        cap = cooling.get_cooling_capacity(0.5, ambient_temp=25.0, server_temp=50.0)
        assert cap > 0.0

    def test_cooling_capacity_zero_flow(self, cooling):
        cap = cooling.get_cooling_capacity(0.0, ambient_temp=25.0, server_temp=50.0)
        assert cap >= 0.0

    def test_cost_info(self, cooling):
        info = cooling.get_cost_info()
        assert 'label' in info
        assert 'capex_per_server_eur' in info

    def test_liquid_higher_capacity_than_air(self):
        air = CoolingSystem('AIR')
        liquid = CoolingSystem('LIQUID')
        air_cap = air.get_cooling_capacity(1.0, 25.0, 50.0)
        liq_cap = liquid.get_cooling_capacity(1.0, 25.0, 50.0)
        assert liq_cap > air_cap

    def test_air_has_higher_midload_power_than_liquid(self):
        air = CoolingSystem('AIR')
        liquid = CoolingSystem('LIQUID')
        assert air.get_power_consumption(0.5) > liquid.get_power_consumption(0.5)

    def test_hybrid_power_sits_between_air_and_liquid(self):
        air = CoolingSystem('AIR')
        liquid = CoolingSystem('LIQUID')
        hybrid = CoolingSystem('HYBRID')
        hybrid_power = hybrid.get_power_consumption(0.6)
        assert air.get_power_consumption(0.6) > hybrid_power > liquid.get_power_consumption(0.6)

    def test_hybrid_has_subsystems(self):
        hybrid = CoolingSystem('HYBRID')
        assert hasattr(hybrid, '_air_sub')
        assert hasattr(hybrid, '_liquid_sub')

    def test_degradation_works(self):
        cooling = CoolingSystem('AIR')
        initial = cooling.efficiency_factor
        for _ in range(10000):
            cooling.update_degradation(dt=3600.0)
        assert cooling.efficiency_factor < initial
        assert cooling.efficiency_factor >= 0.85

class TestServerCoolingMode:

    def test_server_uses_air_from_config(self):
        cfg = DEFAULT_CONFIG
        cfg.cooling.mode = 'AIR'
        server = Server(0, cfg)
        assert server.cooling_system.mode == 'AIR'

    def test_server_uses_liquid_from_config(self):
        cfg = Config()
        cfg.cooling.mode = 'LIQUID'
        server = Server(0, cfg)
        assert server.cooling_system.mode == 'LIQUID'

    def test_server_uses_hybrid_from_config(self):
        cfg = Config()
        cfg.cooling.mode = 'HYBRID'
        server = Server(0, cfg)
        assert server.cooling_system.mode == 'HYBRID'

    def test_server_physics_update(self):
        cfg = Config()
        cfg.cooling.mode = 'LIQUID'
        server = Server(0, cfg)
        server.reset()
        result = server.update_physics(cpu_load=0.5, cooling_action=0.5)
        assert 'temp' in result
        assert 'it_power' in result
        assert 'cooling_power' in result
        assert 'health' in result

class TestDataCenterEnvWithModes:

    @pytest.fixture(params=['AIR', 'LIQUID', 'HYBRID'])
    def env(self, request):
        cfg = Config()
        cfg.cooling.mode = request.param
        env = DataCenterEnv(cfg)
        return env

    def test_env_init(self, env):
        obs, info = env.reset()
        assert obs.shape == env.observation_space.shape
        assert isinstance(obs, np.ndarray)

    def test_env_step(self, env):
        env.reset()
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == env.observation_space.shape
        assert isinstance(reward, float)
        assert 'total_power' in info
        assert 'cooling_power' in info

    def test_energy_first_reward(self, env):
        env.reset()
        low_action = np.full(env.num_servers, 0.2)
        _, reward_low, _, _, info_low = env.step(low_action)
        env.reset()
        high_action = np.full(env.num_servers, 1.0)
        _, reward_high, _, _, info_high = env.step(high_action)
        assert info_low['cooling_power'] < info_high['cooling_power']
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
