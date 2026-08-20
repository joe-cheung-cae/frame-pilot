import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import get_settings, reset_settings_cache
from app.core.local_paths import is_windows_absolute_path, normalize_user_path
from app.core.project_roots import clear_registered_roots, register_root
from app.main import create_app
from app.services.importing import expand_import_paths


def _write_jpeg(path: Path, color=(80, 120, 40)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 24), color=color).save(path, format="JPEG")


def test_normalize_user_path_rejects_nul():
    with pytest.raises(ValueError, match="NUL"):
        normalize_user_path("/tmp/foo\x00bar.jpg")
    with pytest.raises(ValueError, match="NUL"):
        normalize_user_path("C:\\Photos\\\x00a.jpg")


def test_normalize_user_path_strips_trailing_separators_and_keeps_roots():
    assert normalize_user_path("/tmp/photos/") == "/tmp/photos"
    assert normalize_user_path("/tmp/photos//") == "/tmp/photos"
    assert normalize_user_path("/") == "/"
    assert normalize_user_path(r"C:\Photos\\") == r"C:\Photos"
    assert normalize_user_path("C:/Photos/") == r"C:\Photos"
    assert normalize_user_path("C:/") == "C:\\"
    assert normalize_user_path("C:\\") == "C:\\"


def test_normalize_user_path_keeps_spaces_and_non_ascii():
    assert normalize_user_path("/tmp/my photos/写真/") == "/tmp/my photos/写真"
    assert normalize_user_path("D:/My Photos/撮影/") == r"D:\My Photos\撮影"


def test_windows_drive_letters_are_absolute_paths():
    assert is_windows_absolute_path(r"C:\Users\Photos")
    assert is_windows_absolute_path("D:/Photos/a.jpg")
    assert is_windows_absolute_path("C:\\")
    assert is_windows_absolute_path(r"C:\Photos\\")
    assert not is_windows_absolute_path("C:relative")
    assert not is_windows_absolute_path("relative.jpg")
    assert not is_windows_absolute_path("/posix/path")


def test_expand_import_paths_rejects_nul(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    with pytest.raises(ValueError, match="NUL"):
        expand_import_paths([str(tmp_path / "shot.jpg") + "\x00.jpg"], project_root)


def test_expand_import_paths_spaces_non_ascii_and_trailing_sep(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "card with space" / "写真フォルダ"
    jpeg = source / "my 写真.jpg"
    _write_jpeg(jpeg)

    expanded = expand_import_paths([str(source) + os.sep], project_root)

    assert expanded.files == [jpeg.resolve()]


@pytest.mark.skipif(os.name != "nt", reason="Win32 drive-letter filesystem")
def test_expand_import_paths_windows_drive_letter_live(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "My Photos"
    jpeg = source / "a.jpg"
    _write_jpeg(jpeg)
    assert Path(tmp_path).drive

    expanded = expand_import_paths([str(source) + "\\"], project_root)

    assert expanded.files == [jpeg.resolve()]


def test_register_root_rejects_nul(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_registered_roots()
    with pytest.raises(ValueError, match="NUL"):
        register_root(str(tmp_path / "root") + "\x00")


def test_register_root_spaces_non_ascii_and_trailing_sep(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    clear_registered_roots()
    root = tmp_path / "my photos" / "撮影"
    root.mkdir(parents=True)

    registered = register_root(str(root) + os.sep)

    assert registered == root.resolve()
    clear_registered_roots()


def test_create_project_rejects_nul_in_root_path(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    legal = tmp_path / "projects" / "nested"
    legal.mkdir(parents=True)

    response = client.post(
        "/api/projects",
        json={"name": "Nul root", "root_path": str(legal) + "\x00"},
    )

    assert response.status_code == 422
    assert "NUL" in response.json()["detail"]


def test_create_project_spaces_non_ascii_and_trailing_sep(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    root = tmp_path / "projects" / "with space" / "データ"
    root.mkdir(parents=True)

    response = client.post(
        "/api/projects",
        json={"name": "Trail", "root_path": str(root) + os.sep},
    )

    assert response.status_code == 201
    assert Path(response.json()["root_path"]) == root.resolve()


def test_allowlist_parses_os_pathsep_with_spaces_and_non_ascii(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    first = tmp_path / "first allow"
    second = tmp_path / "第二"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir))
    monkeypatch.setenv(
        "FRAMEPILOT_PROJECT_ROOT_ALLOWLIST",
        os.pathsep.join([str(first) + os.sep, str(second)]),
    )
    reset_settings_cache()

    allowlist = get_settings().project_root_allowlist
    assert first.resolve() in allowlist
    assert second.resolve() in allowlist

    client = TestClient(create_app())
    created = client.post("/api/projects", json={"name": "A", "root_path": str(first)})
    assert created.status_code == 201
    created_second = client.post(
        "/api/projects",
        json={"name": "B", "root_path": str(second) + os.sep},
    )
    assert created_second.status_code == 201


def test_allowlist_splits_only_on_os_pathsep(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir))
    monkeypatch.setattr("app.core.config.os.pathsep", "|")
    monkeypatch.setenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", f"{first}|{second}")
    reset_settings_cache()

    roots = {path.resolve() for path in get_settings().project_root_allowlist}
    assert roots == {first.resolve(), second.resolve()}


def test_allowlist_keeps_other_delimiter_inside_a_single_entry(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    other = ";" if os.pathsep == ":" else ":"
    folder = tmp_path / f"allow{other}listed"
    folder.mkdir()
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", str(folder))
    reset_settings_cache()

    assert get_settings().project_root_allowlist == [folder.resolve()]
