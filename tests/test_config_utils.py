from src.utils.config import Config, get_available_config_paths, resolve_config_file


def test_default_is_the_preferred_config():
    assert resolve_config_file().name == 'default.yaml'


def test_available_profiles_match_supported_yaml_set():
    names = {path.name for path in get_available_config_paths()}
    assert names == {'default.yaml', 'hybrid.yaml', 'liquid.yaml'}


def test_default_config_schema_matches_simplified_reward_shape():
    reward_keys = set(Config().to_dict()['reward'])
    environment_keys = set(Config().to_dict()['environment'])

    assert 'energy_efficiency_bonus' not in reward_keys
    assert 'cooling_power_weight' not in reward_keys
    assert 'overcooling_penalty_coefficient' not in reward_keys
    assert 'sweet_spot_low' not in reward_keys
    assert 'sweet_spot_high' not in reward_keys
    assert 'sweet_spot_bonus' not in reward_keys
    assert 'episode_length' not in environment_keys
