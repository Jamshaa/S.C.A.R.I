from src.utils.config import get_available_config_paths, resolve_config_file


def test_optimized_is_the_preferred_config():
    assert resolve_config_file().name == 'optimized.yaml'


def test_available_profiles_match_supported_yaml_set():
    names = {path.name for path in get_available_config_paths()}
    assert 'optimized.yaml' in names
    assert 'max_savings_safe.yaml' in names
    assert 'liquid.yaml' in names
    assert 'hybrid.yaml' in names
    assert 'default.yaml' not in names
