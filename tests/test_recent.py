from pathlib import Path

from ordpaint.core.recent import RecentFiles


def test_recent_files_puts_newest_first_and_deduplicates(tmp_path: Path) -> None:
    recent = RecentFiles(max_items=3)
    first = tmp_path / "first.ordpaint"
    second = tmp_path / "second.ordpaint"

    recent.add(first)
    recent.add(second)
    recent.add(first)

    assert recent.to_list() == [RecentFiles.normalize(first), RecentFiles.normalize(second)]


def test_recent_files_enforces_limit(tmp_path: Path) -> None:
    recent = RecentFiles(max_items=2)
    for index in range(3):
        recent.add(tmp_path / f"{index}.ordpaint")

    assert len(recent.to_list()) == 2
    assert recent.to_list()[0].endswith("2.ordpaint")


def test_recent_files_existing_filters_missing_paths(tmp_path: Path) -> None:
    existing = tmp_path / "saved.ordpaint"
    existing.touch()
    recent = RecentFiles(paths=[str(existing), str(tmp_path / "missing.ordpaint")])

    assert recent.existing() == [RecentFiles.normalize(existing)]


def test_recent_files_remove_and_clear(tmp_path: Path) -> None:
    recent = RecentFiles()
    path = tmp_path / "saved.ordpaint"
    recent.add(path)

    assert recent.remove(path)
    assert not recent.remove(path)
    recent.add(path)
    recent.clear()
    assert recent.to_list() == []
