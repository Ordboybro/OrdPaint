from ordpaint.core.settings import Settings


def test_settings_roundtrip_and_recent_files(tmp_path):
    path = tmp_path / "settings.json"
    image = tmp_path / "image.png"
    image.write_bytes(b"test")

    settings = Settings(path)
    settings.set("window_width", 1600)
    settings.add_recent_file(str(image))
    settings.save()

    loaded = Settings(path)
    assert loaded.get("window_width") == 1600
    assert loaded.recent_files() == [str(image.resolve())]


def test_settings_reject_invalid_types(tmp_path):
    settings = Settings(tmp_path / "settings.json")
    try:
        settings.set("window_width", "wide")
    except TypeError:
        pass
    else:
        raise AssertionError("invalid setting type must be rejected")
