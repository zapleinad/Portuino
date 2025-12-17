import os
import re
import sys
import json
import stat
import shutil
import subprocess
import tempfile
import platform
import zipfile
import tarfile
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple, List

# ======================================================================================
# Arduino CLI bootstrap
# Objetivo: o usuário NÃO precisa instalar o arduino-cli previamente.
# Estratégia:
# 1) Se existir um arduino-cli "embutido" (empacotado junto do executável), usa ele.
# 2) Senão, tenta encontrar no PATH.
# 3) Senão, baixa automaticamente o binário (1ª execução) para um cache do usuário.
#
# Observação:
# - Para compilar/enviar para a placa, o Arduino CLI pode precisar baixar o "core" (ex: arduino:avr).
#   Isso ocorre automaticamente quando você chamar compile/upload, desde que o PC tenha internet na 1ª vez.
# ======================================================================================

def _is_windows() -> bool:
    return platform.system().lower().startswith("win")

def _cache_dir() -> str:
    if _is_windows():
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    d = os.path.join(base, "Portuino", "tools")
    os.makedirs(d, exist_ok=True)
    return d

def _candidate_bundled_paths() -> List[str]:
    exe_name = "arduino-cli.exe" if _is_windows() else "arduino-cli"
    candidates: List[str] = []

    # PyInstaller: onefile/onefolder expõe sys._MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "tools", "arduino-cli", exe_name))
        candidates.append(os.path.join(meipass, exe_name))

    # Ao lado do executável (onefolder)
    exe_dir = os.path.dirname(getattr(sys, "executable", "") or "")
    if exe_dir:
        candidates.append(os.path.join(exe_dir, "tools", "arduino-cli", exe_name))
        candidates.append(os.path.join(exe_dir, exe_name))

    # Em modo "python puro", ao lado deste arquivo
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, "tools", "arduino-cli", exe_name))
    candidates.append(os.path.join(here, exe_name))

    return candidates

def _ensure_executable(path: str) -> None:
    if _is_windows():
        return
    try:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

def _download(url: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PortuinoIDE/1.0 (arduino-cli bootstrap)"},
    )
    with urllib.request.urlopen(req) as r, open(dst, "wb") as f:
        f.write(r.read())

def _select_asset_url(release_json: dict) -> Tuple[str, str]:
    """Retorna (url, filename) do asset do arduino-cli compatível com o SO."""
    assets = release_json.get("assets") or []
    sysname = platform.system().lower()
    arch = platform.machine().lower()

    # Normaliza arch mais comum
    arch64 = arch in ("amd64", "x86_64", "x64")

    if sysname.startswith("win"):
        patterns = ["Windows_64bit.zip", "windows_amd64.zip", "windows_x86_64.zip"]
    elif sysname.startswith("linux"):
        patterns = ["Linux_64bit.tar.gz", "linux_amd64.tar.gz", "linux_x86_64.tar.gz"]
    else:
        raise RuntimeError(f"Sistema operacional não suportado para bootstrap automático: {platform.system()}")

    if not arch64:
        raise RuntimeError(f"Arquitetura não suportada para bootstrap automático: {platform.machine()}")

    for a in assets:
        name = a.get("name", "")
        for p in patterns:
            if p.lower() in name.lower():
                return a.get("browser_download_url", ""), name

    # fallback: tenta qualquer asset que contenha Windows/Linux e 64bit
    for a in assets:
        name = (a.get("name") or "").lower()
        if ("windows" in name or "linux" in name) and ("64" in name) and (name.endswith(".zip") or name.endswith(".tar.gz")):
            return a.get("browser_download_url", ""), a.get("name", "")

    raise RuntimeError("Não encontrei um asset compatível do Arduino CLI no release latest.")

def _download_and_extract_arduino_cli() -> str:
    cache = _cache_dir()
    api_url = "https://api.github.com/repos/arduino/arduino-cli/releases/latest"

    req = urllib.request.Request(api_url, headers={"User-Agent": "PortuinoIDE/1.0"})
    with urllib.request.urlopen(req) as r:
        release = json.loads(r.read().decode("utf-8"))

    url, fname = _select_asset_url(release)
    if not url:
        raise RuntimeError("Release latest encontrado, mas URL de download vazia.")

    pkg_path = os.path.join(cache, fname)
    if not os.path.exists(pkg_path):
        _download(url, pkg_path)

    extract_dir = os.path.join(cache, "arduino-cli")
    os.makedirs(extract_dir, exist_ok=True)

    if fname.lower().endswith(".zip"):
        with zipfile.ZipFile(pkg_path, "r") as z:
            z.extractall(extract_dir)
    elif fname.lower().endswith(".tar.gz"):
        with tarfile.open(pkg_path, "r:gz") as t:
            t.extractall(extract_dir)
    else:
        raise RuntimeError(f"Formato de pacote não suportado: {fname}")

    exe_name = "arduino-cli.exe" if _is_windows() else "arduino-cli"

    # Procura o executável extraído em subpastas
    for root, _, files in os.walk(extract_dir):
        if exe_name in files:
            cli = os.path.join(root, exe_name)
            _ensure_executable(cli)
            return cli

    raise RuntimeError("Baixei e extraí o Arduino CLI, mas não encontrei o executável.")

_ARDUINO_CLI_PATH: Optional[str] = None

def ensure_arduino_cli() -> str:
    """Garante um caminho executável para arduino-cli e retorna esse caminho."""
    global _ARDUINO_CLI_PATH
    if _ARDUINO_CLI_PATH and os.path.exists(_ARDUINO_CLI_PATH):
        return _ARDUINO_CLI_PATH

    # 0) override explícito (útil em depuração)
    override = os.environ.get("PORTUINO_ARDUINO_CLI")
    if override and os.path.exists(override):
        _ensure_executable(override)
        _ARDUINO_CLI_PATH = override
        return override

    # 1) embutido (no bundle)
    for p in _candidate_bundled_paths():
        if os.path.exists(p):
            _ensure_executable(p)
            _ARDUINO_CLI_PATH = p
            return p

    # 2) PATH
    which = shutil.which("arduino-cli")
    if which:
        _ARDUINO_CLI_PATH = which
        return which

    # 3) download 1ª execução
    try:
        _ARDUINO_CLI_PATH = _download_and_extract_arduino_cli()
        return _ARDUINO_CLI_PATH
    except Exception as e:
        raise RuntimeError(
            "Não encontrei o Arduino CLI.
"
            "Tentei: (1) embutido no executável, (2) PATH, (3) download automático.

"
            f"Falha no download automático: {e}

"
            "Alternativas:
"
            "- Instale o Arduino CLI manualmente e reabra a Portuino IDE.
"
            "- Ou defina a variável de ambiente PORTUINO_ARDUINO_CLI apontando para o executável."
        )

def _run(cmd: List[str]) -> Tuple[int, str]:
    """Executa comando retornando (code, stdout+stderr). Substitui arduino-cli pelo caminho detectado."""
    if cmd and cmd[0] == "arduino-cli":
        cmd = [ensure_arduino_cli()] + cmd[1:]

    p = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out

@dataclass
class BuildConfig:
    fqbn: str               # ex: "arduino:avr:uno"
    port: str               # ex: "COM3" ou "/dev/ttyACM0"
    baud: int = 9600

def list_ports_cli() -> str:
    code, out = _run(["arduino-cli", "board", "list"])
    return out

def auto_detect_port_and_fqbn(prefer_fqbn: str = "arduino:avr:uno") -> BuildConfig:
    """
    Tenta detectar porta e FQBN via `arduino-cli board list`.
    Se não achar FQBN, usa prefer_fqbn.
    """
    _ = ensure_arduino_cli()
    code, out = _run(["arduino-cli", "board", "list"])
    if code != 0:
        raise RuntimeError("Falha ao listar placas/portas:\n" + out)

    # Heurística: pega a primeira linha com uma porta COMx ou /dev/tty*
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    port = None
    fqbn = None

    for ln in lines:
        if ln.lower().startswith("port"):
            continue
        m = re.search(r"\b(COM\d+)\b", ln)
        if not m:
            m = re.search(r"(/dev/tty\w+)", ln)
        if m:
            port = m.group(1)
            m2 = re.search(r"\b([a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+)\b", ln)
            if m2:
                fqbn = m2.group(1)
            break

    if not port:
        raise RuntimeError(
            "Não encontrei porta automaticamente.\n"
            "Conecte a placa e confirme a porta na Arduino IDE ou execute `arduino-cli board list`.\n\n"
            + out
        )

    return BuildConfig(fqbn=fqbn or prefer_fqbn, port=port)

# ------------------ PORTUINO -> ARDUINO (.ino) ------------------

def _to_cpp_expr(expr: str) -> str:
    """
    Converte coisas simples:
    - verdadeiro/falso -> true/false
    - concatenação com + em escrever(...) -> String(...)
    """
    expr = expr.strip()
    expr = expr.replace("verdadeiro", "true").replace("falso", "false")

    # Se tem aspas ou +, gera concat String
    if "+" in expr:
        parts = [p.strip() for p in expr.split("+")]
        cpp_parts = []
        for p in parts:
            if p.startswith('"') and p.endswith('"'):
                cpp_parts.append(p)
            elif re.fullmatch(r"\d+(\.\d+)?", p):
                cpp_parts.append(f"String({p})")
            else:
                cpp_parts.append(f"String({p})")
        return " + ".join(cpp_parts)

    return expr

def portuino_to_ino(code_ptn: str, baud: int = 9600) -> str:
    """
    Tradutor simples (educacional) Portuino -> Arduino C++.
    Regras suportadas:
    - inteiro/real/logico/texto
    - x <- expr
    - se(...) entao / senao / fim_se
    - enquanto(...) faca / fim_enquanto
    - para i de A ate B passo P / fim_para
    - configurar_saida(p), configurar_entrada(p)
    - ligar(p), desligar(p), esperar(ms), ler(p)
    - medir_distancia(trig, echo)
    - escrever(...)
    """
    lines = [ln.rstrip() for ln in code_ptn.splitlines()]
    in_prog = False
    body = []

    for ln in lines:
        s = ln.strip()
        if s == "inicio":
            in_prog = True
            continue
        if s == "fim":
            break
        if in_prog:
            if not s or s.startswith("//"):
                continue
            body.append(s)

    # Coleta declarações (bem simples)
    decls = []
    stmts = []

    type_map = {"inteiro": "int", "real": "float", "logico": "bool", "texto": "String"}

    for s in body:
        m = re.match(r"^(inteiro|real|logico|texto)\s+(\w+)\s*<-\s*(.+)$", s)
        if m:
            t, var, val = m.group(1), m.group(2), m.group(3)
            decls.append(f"{type_map[t]} {var} = {_to_cpp_expr(val)};")
        else:
            stmts.append(s)

    def tr(s: str) -> str:
        # atribuição
        m = re.match(r"^(\w+)\s*<-\s*(.+)$", s)
        if m:
            return f"{m.group(1)} = {_to_cpp_expr(m.group(2))};"

        # controle
        m = re.match(r"^se\s*\((.*)\)\s*entao$", s)
        if m:
            return f"if ({_to_cpp_expr(m.group(1))}) {{"

        if s == "senao":
            return "} else {"

        if s == "fim_se":
            return "}"

        m = re.match(r"^enquanto\s*\((.*)\)\s*faca$", s)
        if m:
            return f"while ({_to_cpp_expr(m.group(1))}) {{"

        if s == "fim_enquanto":
            return "}"

        m = re.match(r"^para\s+(\w+)\s+de\s+(.*)\s+ate\s+(.*)\s+passo\s+(.*)$", s)
        if m:
            var, a, b, p = m.group(1), m.group(2), m.group(3), m.group(4)
            a, b, p = _to_cpp_expr(a), _to_cpp_expr(b), _to_cpp_expr(p)
            return f"for (int {var} = {a}; {var} <= {b}; {var} += {p}) {{"



        if s == "fim_para":
            return "}"

        # funções arduino
        m = re.match(r"^configurar_saida\((.*)\)$", s)
        if m:
            return f"pinMode({m.group(1)}, OUTPUT);"

        m = re.match(r"^configurar_entrada\((.*)\)$", s)
        if m:
            return f"pinMode({m.group(1)}, INPUT);"

        m = re.match(r"^ligar\((.*)\)$", s)
        if m:
            return f"digitalWrite({m.group(1)}, HIGH);"

        m = re.match(r"^desligar\((.*)\)$", s)
        if m:
            return f"digitalWrite({m.group(1)}, LOW);"

        m = re.match(r"^esperar\((.*)\)$", s)
        if m:
            return f"delay((int)({_to_cpp_expr(m.group(1))}));"

        m = re.match(r"^escrever\((.*)\)$", s)
        if m:
            expr = _to_cpp_expr(m.group(1))
            return f"Serial.println({expr});"

        # fallback: permite escrever C++ direto (educacional avançado)
        return s + (";" if not s.endswith((";", "{", "}")) else "")

    translated = [tr(s) for s in stmts]

    # adiciona biblioteca runtime do ultrassom:
    runtime = f"""
/*
  Sketch gerado pela Portuino IDE
*/
long medir_distancia(int trig, int echo) {{
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long dur = pulseIn(echo, HIGH, 30000); // timeout ~30ms
  long cm = dur / 58; // aproximação
  return cm;
}}
"""

    ino = f"""
{runtime}

void setup() {{
  Serial.begin({baud});
}}

void loop() {{
  // Declarações (re-inicializam a cada loop; educativo)
  {' '.join(decls)}

  // Código Portuino
  {os.linesep.join(translated)}
}}
""".strip() + "\n"

    return ino

def compile_sketch(code_ptn: str, cfg: BuildConfig) -> Tuple[str, str]:
    """
    Retorna (build_dir, logs)
    """
    ensure_arduino_cli()
    ino = portuino_to_ino(code_ptn, baud=cfg.baud)

    workdir = os.path.join(tempfile.gettempdir(), "portuino_sketch")
    os.makedirs(workdir, exist_ok=True)
    ino_path = os.path.join(workdir, "portuino_sketch.ino")
    with open(ino_path, "w", encoding="utf-8") as f:
        f.write(ino)

    cmd = ["arduino-cli", "compile", "--fqbn", cfg.fqbn, workdir]
    code, out = _run(cmd)
    if code != 0:
        raise RuntimeError("Erro ao compilar:\n" + out)
    return workdir, out

def upload_sketch(code_ptn: str, cfg: BuildConfig) -> str:
    ensure_arduino_cli()
    workdir, logs = compile_sketch(code_ptn, cfg)
    cmd = ["arduino-cli", "upload", "-p", cfg.port, "--fqbn", cfg.fqbn, workdir]
    code, out = _run(cmd)
    if code != 0:
        raise RuntimeError("Erro ao fazer upload:\n" + out)
    return logs + "\n" + out
