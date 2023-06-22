from app.settings import flatten_settings_values


def test_flatten_settings_values(example_settings):
    values = flatten_settings_values(example_settings)
    assert values == {"app", "model", "secret", "world"}
