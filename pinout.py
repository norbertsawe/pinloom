#!/usr/bin/env python3
import json
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

# High-contrast escape definitions
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

# Remote centralized database archive URL
REMOTE_TARBALL_URL = "https://github.com/norbertsawe/pinout-pages/archive/refs/heads/main.tar.gz"

# Standard XDG Data Location (~/.local/share/pinout/database)
XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
DATA_DIR = Path(XDG_DATA_HOME) / "pinout"
DB_DIR = DATA_DIR / "database"


def update_database():
    """Fetches the latest centralized database definitions from GitHub."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tarball_path = DATA_DIR / "db_temp.tar.gz"

    print(f"\n{CYAN}{BOLD}🔄 Syncing pinout database from remote...{RESET}")
    try:
        urllib.request.urlretrieve(REMOTE_TARBALL_URL, tarball_path)

        with tarfile.open(tarball_path, "r:gz") as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts
                # Look for files inside the database/ directory of the repo
                if len(parts) > 1 and parts[1] == "database":
                    target_path = DB_DIR / Path(*parts[2:])
                    if member.isdir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with tar.extractfile(member) as src, open(target_path, "wb") as dst:
                            dst.write(src.read())

        if tarball_path.exists():
            tarball_path.unlink()

        print(f"{GREEN}{BOLD}✓ Database updated successfully!{RESET}\n")
    except Exception as e:
        print(f"{RED}[!] Failed to update database: {e}{RESET}\n", file=sys.stderr)


def load_database():
    """Dynamically parses all JSON library maps inside the XDG database directory."""
    database = {}

    if not DB_DIR.exists() or not any(DB_DIR.iterdir()):
        print(f"{YELLOW}[!] Local database is empty. Running initial sync...{RESET}")
        update_database()

    if not DB_DIR.exists():
        return database

    for filepath in DB_DIR.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                database.update(file_data)
        except Exception:
            pass

    # Append aliases dynamically
    if "dht11" in database:
        database["dht22"] = database["dht11"]
    if "stm32" in database:
        database["bluepill"] = database["stm32"]
    if "esp8266" in database:
        database["nodemcu"] = database["esp8266"]
    if "hcsr04" in database:
        database["hc-sr04"] = database["hcsr04"]
    if "esp32s3" in database:
        database["esp32-s3"] = database["esp32s3"]

    return database


def about_tool():
    """Prints a brief metadata summary about the tool's goal."""
    print(f"\n{CYAN}{BOLD}ℹ️  About pinout-cli{RESET}")
    print("--------------------------------------------------")
    print("A blazing-fast, lightweight, offline hardware pinout dictionary.")
    print("Designed for engineering students and electronics makers to check")
    print("IC footprint configurations instantly without dragging down the workflow")
    print("or searching through endless manufacturer datasheets under a microscope.")
    print(f"\n{YELLOW}Version:{RESET} 1.2.0 (Centralized Engine)")
    print(f"{YELLOW}License:{RESET} MIT")
    print(f"{YELLOW}Local Cache:{RESET} {DB_DIR}")
    print("--------------------------------------------------\n")


def print_help(db):
    """Renders a comprehensive interface index of found chips."""
    print(f"\n{GREEN}{BOLD}pinout-cli — Modular Hardware Pinout Lookup Tool{RESET}")
    print(f"{BOLD}Usage:{RESET} pinout <chip-name>")
    print(f"       pinout [options]")
    print(f"\n{BOLD}Options:{RESET}")
    print("  -u, --update        Fetch the latest central database definitions")
    print("  -h, --help          Show this index help sheet and exit")
    print("  -a, --about         Show info about the tool project parameters")
    print(f"\n{BOLD}Available Components In Local Cache ({DB_DIR}):{RESET}")

    keys = sorted(list(db.keys()))
    aliases = ["dht22", "bluepill", "nodemcu", "hc-sr04", "esp32-s3"]
    keys = [k for k in keys if k not in aliases]

    if not keys:
        print(f"  {RED}(No components found. Run 'pinout --update' to populate cache){RESET}")
    else:
        for i in range(0, len(keys), 4):
            chunk = keys[i:i+4]
            print("  " + "".join(f"{k:<15}" for k in chunk))

    print(f"\n{CYAN}💡 Pro-Tip:{RESET} Run {BOLD}pinout --update{RESET} regularly to pull newly added community definitions!\n")


def main():
    if len(sys.argv) < 2:
        db = load_database()
        print_help(db)
        sys.exit(0)

    raw_query = sys.argv[1].lower().strip()

    if raw_query in ["-u", "--update", "update"]:
        update_database()
        sys.exit(0)

    if raw_query in ["-a", "--about", "about"]:
        about_tool()
        return

    if raw_query in ["-h", "--help", "help"]:
        db = load_database()
        print_help(db)
        return

    db = load_database()

    # Process standard hardware query normalization
    query = raw_query.replace("-", "").replace(" ", "")

    if query in db:
        chip = db[query]
        print(f"\n{GREEN}{BOLD}=== {chip['name']} ==={RESET}")
        print(f"{CYAN}Info:{RESET} {chip['description']}")
        print(chip['ascii_art'])
    else:
        print(f"\n{RED}[!] Error: Component variant '{sys.argv[1]}' is unrecognized.{RESET}")
        print_help(db)


if __name__ == "__main__":
    main()
