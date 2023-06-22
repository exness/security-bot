from app.secbot.config import get_jsonpath_value


def test_config_get_jsonpath_value():
    meaning_of_the_universe = 42
    data = {"base": {"deep": {"deeper": {"here": meaning_of_the_universe}}}}
    assert get_jsonpath_value(data, "base.deep.deeper.here") == meaning_of_the_universe
