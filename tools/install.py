"""Install Pinloom for the current user and configure command discovery.

This bootstrap uses only the standard library. It deliberately does not import
Pinloom, so it also works before the application or its dependencies are installed.
"""

from __future__ import annotations

import argparse
import ntpath
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "# >>> Pinloom PATH >>>"
END = "# <<< Pinloom PATH <<<"


def locations(home: Path, platform: str, env) -> tuple[Path, Path]:
    if platform == "win32":
        base = Path(env.get("LOCALAPPDATA", home / "AppData" / "Local")) / "Pinloom"
        return base / "venv", base / "bin"
    if platform == "darwin":
        base = home / "Library" / "Application Support" / "pinloom"
    else:
        base = Path(env.get("XDG_DATA_HOME", home / ".local" / "share")) / "pinloom"
    return base / "venv", home / ".local" / "bin"


def shell_block(binary_dir: Path, *, fish: bool = False) -> str:
    value = str(binary_dir)
    if any(c in value for c in "\n\r:"):
        raise ValueError("PATH directories cannot contain colons or line breaks")
    if fish:
        quoted = "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
        body = f"if not contains -- {quoted} $PATH\n    set -gx PATH {quoted} $PATH\nend"
    else:
        quoted = shlex.quote(value)
        body = (
            f'case ":${{PATH-}}:" in\n  *:{quoted}:*) ;;\n'
            f'  *) export PATH={quoted}:"${{PATH-}}" ;;\nesac'
        )
    return f"{START}\n{body}\n{END}\n"


def update_profile(path: Path, block: str):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
    if START in text:
        if not pattern.search(text):
            raise ValueError(f"incomplete Pinloom PATH block in {path}; repair it before retrying")
        updated = pattern.sub(lambda _: block, text)
    else:
        updated = text + ("\n" if text and not text.endswith("\n") else "") + block
    if updated != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")


def configure_posix_path(home: Path, binary_dir: Path, env) -> list[Path]:
    zsh_home = Path(env.get("ZDOTDIR", home))
    # Bash reads only the first existing login profile, while interactive shells
    # use .bashrc. zsh uses ZDOTDIR when configured. Fish reads conf.d scripts.
    bash_login = next(
        (home / n for n in (".bash_profile", ".bash_login") if (home / n).exists()),
        home / ".profile",
    )
    profiles = list(
        dict.fromkeys(
            [
                home / ".profile",
                bash_login,
                home / ".bashrc",
                zsh_home / ".zprofile",
                zsh_home / ".zshrc",
            ]
        )
    )
    block = shell_block(binary_dir)
    for path in profiles:
        update_profile(path, block)
    fish = Path(env.get("XDG_CONFIG_HOME", home / ".config")) / "fish/conf.d/pinloom.fish"
    update_profile(fish, shell_block(binary_dir, fish=True))
    return profiles + [fish]


def windows_path(old: str, binary_dir: str) -> str:
    def normalized(value):
        return ntpath.normcase(ntpath.normpath(ntpath.expandvars(value.strip().strip('"'))))

    if any(normalized(p) == normalized(binary_dir) for p in old.split(";") if p.strip()):
        return old
    return binary_dir + (";" + old if old else "")


def configure_windows_path(binary_dir: Path):
    import ctypes
    import winreg
    from ctypes import wintypes

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        try:
            old, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            old, kind = "", winreg.REG_EXPAND_SZ
        updated = windows_path(old, str(binary_dir))
        if updated == old:
            return
        winreg.SetValueEx(key, "Path", 0, kind, updated)
    # Notify Explorer so subsequently launched terminals inherit the new user PATH.
    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPCWSTR,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    send.restype = wintypes.LPARAM
    result = ctypes.c_size_t()
    send(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(result))


def install(source: Path, environment: Path, binary_dir: Path, *, yaml: bool = True):
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    windows = sys.platform == "win32"
    scripts = environment / ("Scripts" if windows else "bin")
    python = scripts / ("python.exe" if windows else "python")
    spec = str(source) + ("[yaml]" if yaml else "")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", spec], check=True)
    executable = scripts / ("pinloom.exe" if windows else "pinloom")
    subprocess.run([str(executable), "--version"], check=True)
    binary_dir.mkdir(parents=True, exist_ok=True)
    target = binary_dir / executable.name
    if target.is_symlink():
        if target.resolve() != executable.resolve():
            raise ValueError(
                f"{target} points to another installation; remove it or choose --bin-dir"
            )
    elif target.exists() and not windows:
        raise ValueError(f"{target} already exists; choose --bin-dir instead of overwriting it")
    if windows:
        # pip's Windows console launcher contains the absolute venv interpreter
        # path. Copy that native launcher; do not put python/pip themselves on PATH.
        shutil.copy2(executable, target)
    elif not target.is_symlink():
        target.symlink_to(executable)
    return target


def main(argv=None):
    if sys.version_info < (3, 10):
        print("Pinloom needs Python 3.10 or newer. Install it and rerun setup.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-path", action="store_true", help="skip persistent PATH changes")
    parser.add_argument(
        "--path-only", action="store_true", help="repair PATH for an existing install"
    )
    parser.add_argument(
        "--no-yaml", action="store_true", help="install without optional YAML support"
    )
    parser.add_argument("--install-dir", type=Path, help="override the private virtual environment")
    parser.add_argument(
        "--bin-dir", type=Path, help="override the directory containing the command"
    )
    args = parser.parse_args(argv)
    environment, binary_dir = locations(Path.home(), sys.platform, os.environ)
    environment = (args.install_dir or environment).expanduser().absolute()
    binary_dir = (args.bin_dir or binary_dir).expanduser().absolute()
    try:
        if args.path_only:
            command = binary_dir / ("pinloom.exe" if sys.platform == "win32" else "pinloom")
            if not command.is_file():
                raise ValueError(f"no installed command at {command}; run setup first")
        else:
            command = install(ROOT, environment, binary_dir, yaml=not args.no_yaml)
        if not args.no_path:
            if sys.platform == "win32":
                configure_windows_path(binary_dir)
                print("Added Pinloom to your persistent Windows user PATH.")
            else:
                profiles = configure_posix_path(Path.home(), binary_dir, os.environ)
                print("Configured PATH in: " + ", ".join(str(p) for p in profiles))
        print(f"Installed command: {command}")
        print("Open a new terminal, then run: pinloom --version")
        if sys.platform != "win32":
            print(f'For this bash/zsh session: export PATH={shlex.quote(str(binary_dir))}:"$PATH"')
            print(f"For this fish session: fish_add_path {shlex.quote(str(binary_dir))}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Pinloom setup failed: {exc}", file=sys.stderr)
        print(
            "Check that Python 3.10+, venv/ensurepip and internet access are available. "
            "On Debian/Ubuntu, install python3-venv if venv creation fails.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
