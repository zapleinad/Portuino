import os, sys, json, shutil, platform, stat, tarfile, zipfile, tempfile
from pathlib import Path
from urllib.request import Request, urlopen

APP_NAME = "PortuinoIDE"
GITHUB_API_LATEST = "https://api.github.com/repos/arduino/arduino-cli/releases/latest"

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)

def bundled_base_dir() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent

def appdata_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME

def tools_dir() -> Path:
    d = appdata_dir() / "tools"
    d.mkdir(parents=True, exist_ok=True)
    return d

def cli_filename() -> str:
    return "arduino-cli.exe" if os.name == "nt" else "arduino-cli"

def cli_path_candidates():
    exe = cli_filename()
    # 1) PATH
    p = shutil.which(exe)
    if p:
        yield Path(p)
    # 2) embutido (se existir)
    yield bundled_base_dir() / "tools" / exe
    # 3) instalado via bootstrap
    yield tools_dir() / exe

def ensure_cli(download_if_missing=True) -> Path:
    for p in cli_path_candidates():
        if p.exists():
            return p
    if not download_if_missing:
        raise RuntimeError("arduino-cli não encontrado e download desabilitado.")
    return download_and_install_latest_cli()

def ensure_cli_config() -> Path:
    cfg = appdata_dir() / "arduino-cli.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.exists():
        data_dir = appdata_dir() / "arduino-data"
        dl_dir = appdata_dir() / "arduino-downloads"
        user_dir = appdata_dir() / "arduino-user"
        data_dir.mkdir(parents=True, exist_ok=True)
        dl_dir.mkdir(parents=True, exist_ok=True)
        user_dir.mkdir(parents=True, exist_ok=True)
        cfg.write_text(
            "directories:\n"
            f"  data: {data_dir.as_posix()}\n"
            f"  downloads: {dl_dir.as_posix()}\n"
            f"  user: {user_dir.as_posix()}\n",
            encoding="utf-8"
        )
    return cfg

def _http_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": f"{APP_NAME}/1.0"})
    with urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def _select_asset(assets: list[dict]) -> dict:
    sysname = platform.system().lower()
    mach = platform.machine().lower()
    is_arm64 = mach in ("aarch64", "arm64")
    is_x64 = mach in ("x86_64", "amd64")

    def score(name: str) -> int:
        n = name.lower()
        s = 0
        if sysname == "windows" and "windows" in n and n.endswith(".zip"):
            s += 60
        if sysname == "linux" and "linux" in n and n.endswith(".tar.gz"):
            s += 60
        if is_arm64 and ("arm64" in n or "aarch64" in n):
            s += 20
        if is_x64 and ("64bit" in n or "amd64" in n or "x86_64" in n):
            s += 20
        if ("32bit" in n or "i386" in n) and (is_x64 or is_arm64):
            s -= 30
        return s

    best, best_s = None, -10**9
    for a in assets:
        sc = score(a.get("name", ""))
        if sc > best_s:
            best_s, best = sc, a

    if not best or best_s < 60:
        raise RuntimeError("Não consegui identificar o pacote correto do arduino-cli para este SO/CPU.")
    return best

def download_and_install_latest_cli() -> Path:
    rel = _http_json(GITHUB_API_LATEST)
    asset = _select_asset(rel.get("assets", []))
    url = asset["browser_download_url"]
    name = asset["name"]

    dest = tools_dir() / cli_filename()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        archive = td / name

        req = Request(url, headers={"User-Agent": f"{APP_NAME}/1.0"})
        with urlopen(req) as r, open(archive, "wb") as f:
            f.write(r.read())

        if name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive, "r") as z:
                z.extractall(td)
        elif name.lower().endswith(".tar.gz"):
            with tarfile.open(archive, "r:gz") as t:
                t.extractall(td)
        else:
            raise RuntimeError(f"Formato não suportado: {name}")

        exe = cli_filename()
        found = None
        for p in td.rglob(exe):
            found = p
            break
        if not found and os.name != "nt":
            for p in td.rglob("arduino-cli"):
                found = p
                break
        if not found:
            raise RuntimeError("Baixei o pacote, mas não encontrei o binário arduino-cli dentro dele.")

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(found, dest)

    if os.name != "nt":
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return dest
