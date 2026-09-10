import json
from pathlib import Path

import pytest

from ordpaint.core.project import ProjectError, load_project


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"{}",
        b"[]",
        b"not-json",
        json.dumps({"format": "wrong", "version": 1}).encode(),
        json.dumps({"format": "ordpaint", "version": 999}).encode(),
        json.dumps({"format": "ordpaint", "version": 1, "width": -1, "height": 10, "layers": []}).encode(),
        json.dumps({"format": "ordpaint", "version": 1, "width": 10**12, "height": 10**12, "layers": []}).encode(),
    ],
)
def test_malformed_project_inputs_raise_project_error(tmp_path: Path, payload: bytes) -> None:
    path = tmp_path / "broken.ordpaint"
    path.write_bytes(payload)
    with pytest.raises(ProjectError):
        load_project(path)
