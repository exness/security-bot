from app.main import sanitize_event_values
from app.settings import flatten_settings_values


def test_sanitize_event_values(example_settings):
    example_event = {
        "exceptions": {
            "values": [
                "Hello, world",
                "Hello, app",
            ],
            "val": "Today in app we rule the world",
        }
    }
    values = flatten_settings_values(example_settings)
    assert sanitize_event_values(
        value=example_event,
        # Sensitive words: world, app, model, secret
        sensitive_values=values,
    ) == {
        "exceptions": {
            "values": ["Hello, [Redacted]", "Hello, [Redacted]"],
            "val": "Today in [Redacted] we rule the [Redacted]",
        }
    }
