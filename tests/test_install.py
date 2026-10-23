"""PATH persistence, quoting, and repeat installs are observable installer behavior."""

import os
import shutil
import subprocess
from pathlib import PurePosixPath

import pytest

from tools.install import (
    END,
    START,
    configure_posix_path,
    locations,
    shell_block,
    update_profile,
    windows_path,
)


def test_platform_install_locations(tmp_path):
    assert locations(tmp_path, "linux", {}) == (
        tmp_path / ".local/share/pinloom/venv",
        tmp_path / ".local/bin",
    )
    assert locations(tmp_path, "darwin", {}) == (
        tmp_path / "Library/Application Support/pinloom/venv",
        tmp_path / ".local/bin",
    )
    assert locations(tmp_path, "win32", {"LOCALAPPDATA": str(tmp_path / "Local")}) == (
        tmp_path / "Local/Pinloom/venv",
        tmp_path / "Local/Pinloom/bin",
    )
    assert locations(tmp_path, "linux", {"XDG_DATA_HOME": str(tmp_path / "data")})[0] == (
        tmp_path / "data/pinloom/venv"
    )


def test_profile_updates_preserve_user_content_and_do_not_duplicate(tmp_path):
    profile = tmp_path / ".zshrc"
    profile.write_text("# My settings\nexport EDITOR=vim\n", encoding="utf-8")
    block = shell_block(PurePosixPath("/home/O'Brien/User Applications/bin"))
    update_profile(profile, block)
    first = profile.read_bytes()
    update_profile(profile, block)
    assert profile.read_bytes() == first
    assert profile.read_text().startswith("# My settings\nexport EDITOR=vim\n")
    assert profile.read_text().count(START) == profile.read_text().count(END) == 1
    update_profile(profile, shell_block(PurePosixPath("/new/bin")))
    assert profile.read_text().count(START) == 1
    assert "O'Brien" not in profile.read_text()
    assert "/new/bin" in profile.read_text()


def test_incomplete_managed_block_is_not_overwritten(tmp_path):
    path = tmp_path / ".profile"
    path.write_text("# existing settings\n" + START + "\n", encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="incomplete"):
        update_profile(path, shell_block(PurePosixPath("/new/bin")))
    assert path.read_bytes() == original


def test_bash_login_zdotdir_and_fish_config_are_respected(tmp_path):
    (tmp_path / ".bash_profile").write_text("# existing bash login\n", encoding="utf-8")
    zsh = tmp_path / "zsh-config"
    xdg = tmp_path / "xdg-config"
    files = configure_posix_path(
        tmp_path,
        PurePosixPath("/home/test/.local/bin"),
        {"ZDOTDIR": str(zsh), "XDG_CONFIG_HOME": str(xdg)},
    )
    assert tmp_path / ".bash_profile" in files
    assert zsh / ".zshrc" in files
    assert zsh / ".zprofile" in files
    assert xdg / "fish/conf.d/pinloom.fish" in files
    assert not (tmp_path / ".zshrc").exists()
    assert "existing bash login" in (tmp_path / ".bash_profile").read_text()
    assert "if not contains --" in files[-1].read_text()
    before = {p: p.read_bytes() for p in files}
    configure_posix_path(
        tmp_path,
        PurePosixPath("/home/test/.local/bin"),
        {"ZDOTDIR": str(zsh), "XDG_CONFIG_HOME": str(xdg)},
    )
    assert before == {p: p.read_bytes() for p in files}


@pytest.mark.parametrize(
    "old",
    [
        r"C:\Windows\System32",
        "",
        r"C:\Tools;C:\Windows\System32;",
        "%SystemRoot%\\System32;C:\\Tools",
    ],
)
def test_windows_path_preserves_existing_entries_and_is_idempotent(old):
    directory = r"C:\Users\Name With Spaces\AppData\Local\Pinloom\bin"
    result = windows_path(old, directory)
    assert result == directory + (";" + old if old else "")
    assert windows_path(result, directory.lower().replace("\\", "/") + "/") == result


def test_windows_path_matches_existing_expandable_environment_entry(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Alice\AppData\Local")
    old = r"C:\Tools;%LOCALAPPDATA%\Pinloom\bin;C:\Windows"
    assert windows_path(old, r"c:\users\alice\appdata\local\pinloom\bin") == old


@pytest.mark.skipif(os.name == "nt", reason="requires a POSIX shell")
@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_actual_shells_load_quoted_paths_without_duplicates(tmp_path, shell):
    executable = shutil.which(shell)
    if not executable:
        pytest.skip(f"{shell} is not installed")
    directory = tmp_path / "O'Brien $test with spaces" / "bin"
    directory.mkdir(parents=True)
    command = directory / "pinloom-path-test"
    command.write_text("#!/bin/sh\nprintf 'discovered'\n", encoding="utf-8")
    command.chmod(0o755)
    profile = tmp_path / "profile"
    update_profile(profile, shell_block(directory, fish=shell == "fish"))
    script = (
        'source "$argv[1]"; source "$argv[1]"; pinloom-path-test'
        if shell == "fish"
        else '. "$1"; . "$1"; pinloom-path-test'
    )
    args = (
        [executable, "-c", script, str(profile)]
        if shell == "fish"
        else [executable, "-c", script, "test", str(profile)]
    )
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    assert result.stdout == "discovered"


@pytest.mark.skipif(
    os.name != "nt", reason="requires Windows registry and native environment notification"
)
def test_windows_registry_update_preserves_type_and_long_path_without_touching_user_path(
    tmp_path, monkeypatch
):
    import uuid
    import winreg

    from tools.install import configure_windows_path

    key_name = r"Software\PinloomInstallerTest-" + uuid.uuid4().hex
    create_key = winreg.CreateKey
    set_value = winreg.SetValueEx
    old = r"%SystemRoot%\System32;" + ";".join(rf"C:\Existing Tools\Tool{i}" for i in range(100))
    with create_key(winreg.HKEY_CURRENT_USER, key_name) as key:
        set_value(key, "Path", 0, winreg.REG_EXPAND_SZ, old)
    calls = []

    def redirected_create(root, name):
        assert root == winreg.HKEY_CURRENT_USER and name == "Environment"
        return create_key(root, key_name)

    def recorded_set(*args):
        calls.append(args[1:])
        return set_value(*args)

    monkeypatch.setattr(winreg, "CreateKey", redirected_create)
    monkeypatch.setattr(winreg, "SetValueEx", recorded_set)
    directory = tmp_path / "User Commands"
    try:
        configure_windows_path(directory)
        configure_windows_path(directory)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name) as key:
            updated, kind = winreg.QueryValueEx(key, "Path")
        assert updated == str(directory) + ";" + old
        assert kind == winreg.REG_EXPAND_SZ
        assert len(calls) == 1
    finally:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_name)
