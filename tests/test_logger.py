from app import format_extra


def test_format_with_extra(faker):
    message = faker.pystr()
    extra = {"hello": "app"}
    assert format_extra(message, extra) == f"{message} EXTRA: hello=app"


def test_format_without_extra(faker):
    message = faker.pystr()
    assert format_extra(message, None) == f"{message}"
