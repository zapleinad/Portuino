# interpretador_portuino.py
# Portuino (interpretador educacional) + integração Arduino real via PyFirmata
# Recomendado: Python 3.10

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# --- Arduino real (PyFirmata) ---
try:
    import serial.tools.list_ports
    from pyfirmata import Arduino, util, INPUT, OUTPUT
    _HAS_FIRMATA = True
except Exception:
    _HAS_FIRMATA = False


# ===============================
# Conexão com Arduino (auto)
# ===============================

@dataclass
class ArduinoContext:
    modo: str  # "REAL" ou "SIMULACAO"
    porta: Optional[str] = None
    board: Any = None
    iterator: Any = None


def _porta_parece_arduino(desc: str, manuf: str, dev: str) -> bool:
    s = f"{desc} {manuf} {dev}".lower()
    # Heurísticas comuns no Windows/Linux
    chaves = [
        "arduino", "wch", "ch340", "cp210", "cp210x", "silicon labs",
        "usb serial", "usb-serial", "ftdi", "ft232", "ttyusb", "ttyacm"
    ]
    return any(k in s for k in chaves)


def encontrar_porta_arduino() -> str:
    if not _HAS_FIRMATA:
        raise RuntimeError("PyFirmata/pyserial não disponíveis.")

    portas = list(serial.tools.list_ports.comports())
    if not portas:
        raise RuntimeError("Nenhuma porta serial encontrada. Conecte o Arduino via USB.")

    # 1) tenta reconhecer pelo texto
    for p in portas:
        desc = getattr(p, "description", "") or ""
        manuf = getattr(p, "manufacturer", "") or ""
        dev = getattr(p, "device", "") or ""
        if _porta_parece_arduino(desc, manuf, dev):
            return p.device

    # 2) fallback: primeira porta
    return portas[0].device


def conectar_arduino_auto() -> ArduinoContext:
    if not _HAS_FIRMATA:
        return ArduinoContext(modo="SIMULACAO")

    try:
        porta = encontrar_porta_arduino()
        board = Arduino(porta)
        it = util.Iterator(board)
        it.start()
        return ArduinoContext(modo="REAL", porta=porta, board=board, iterator=it)
    except Exception:
        # Falhou: não trava a IDE — cai em simulação
        return ArduinoContext(modo="SIMULACAO")


# Contexto global (a IDE importa este módulo)
ARD = conectar_arduino_auto()


# ===============================
# Estado do interpretador
# ===============================

variaveis: Dict[str, Any] = {}
pinos_configurados: Dict[int, str] = {}  # {pino: "saida"/"entrada"}
pinos_sim: Dict[int, int] = {}           # simulação {pino: 0/1}


# ===============================
# Funções "Portuino"
# ===============================

def _log_info(msg: str) -> None:
    print(msg)

def _modo_real() -> bool:
    return ARD.modo == "REAL" and ARD.board is not None


def configurar_saida(pino: int) -> None:
    pino = int(pino)
    if pino in pinos_configurados and pinos_configurados[pino] == "saida":
        return

    if _modo_real():
        ARD.board.digital[pino].mode = OUTPUT
        # opcional: desativa reporting
        try:
            ARD.board.digital[pino].disable_reporting()
        except Exception:
            pass
    else:
        pinos_sim[pino] = pinos_sim.get(pino, 0)

    pinos_configurados[pino] = "saida"
    _log_info(f"[CONFIG] PINO {pino} configurado como SAÍDA ({ARD.modo})")


def configurar_entrada(pino: int) -> None:
    pino = int(pino)
    if pino in pinos_configurados and pinos_configurados[pino] == "entrada":
        return

    if _modo_real():
        ARD.board.digital[pino].mode = INPUT
        # Para read() funcionar no Firmata, é bom habilitar reporting
        try:
            ARD.board.digital[pino].enable_reporting()
        except Exception:
            pass
    else:
        pinos_sim[pino] = pinos_sim.get(pino, 0)

    pinos_configurados[pino] = "entrada"
    _log_info(f"[CONFIG] PINO {pino} configurado como ENTRADA ({ARD.modo})")


def ligar(pino: int) -> None:
    pino = int(pino)
    if _modo_real():
        ARD.board.digital[pino].write(1)
    else:
        pinos_sim[pino] = 1
    _log_info(f"[PIN {pino}] = ALTO (ligado) ({ARD.modo})")


def desligar(pino: int) -> None:
    pino = int(pino)
    if _modo_real():
        ARD.board.digital[pino].write(0)
    else:
        pinos_sim[pino] = 0
    _log_info(f"[PIN {pino}] = BAIXO (desligado) ({ARD.modo})")


def ler(pino: int) -> int:
    """
    Pode ser usado dentro de expressões: ler(2) -> 0/1
    """
    pino = int(pino)

    if _modo_real():
        v = ARD.board.digital[pino].read()
        # read() pode retornar None se ainda não chegou atualização
        if v is None:
            return 0
        return 1 if bool(v) else 0

    return int(bool(pinos_sim.get(pino, 0)))


def medir_distancia(trig: int, echo: int) -> int:
    """
    Ultrassom HC-SR04 via Firmata é LIMITADO.
    Funciona melhor no modo 'Upload' (gerando .ino). Aqui é uma tentativa por polling.

    Retorna distância em cm (aprox). Em SIMULAÇÃO retorna 0.
    """
    trig = int(trig)
    echo = int(echo)

    if not _modo_real():
        return 0

    # Garante modos
    configurar_saida(trig)
    configurar_entrada(echo)

    # Pulso de trigger (10us)
    ARD.board.digital[trig].write(0)
    time.sleep(0.002)
    ARD.board.digital[trig].write(1)
    time.sleep(0.00001)
    ARD.board.digital[trig].write(0)

    # Espera subida do echo
    t0 = time.perf_counter()
    while True:
        v = ARD.board.digital[echo].read()
        if v:
            break
        if (time.perf_counter() - t0) > 0.03:  # ~30ms timeout
            return 0

    # Mede duração alta
    t1 = time.perf_counter()
    while True:
        v = ARD.board.digital[echo].read()
        if not v:
            break
        if (time.perf_counter() - t1) > 0.03:
            break

    dt = time.perf_counter() - t1
    cm = (dt * 34300.0) / 2.0
    return int(cm)


# ===============================
# Avaliador de expressões
# ===============================

def _split_plus_outside_quotes(expr: str) -> List[str]:
    """
    Divide por '+' ignorando '+' dentro de aspas.
    Simples e suficiente para o uso educacional.
    """
    parts = []
    cur = []
    in_str = False
    esc = False

    for ch in expr:
        if esc:
            cur.append(ch)
            esc = False
            continue

        if ch == "\\":
            cur.append(ch)
            esc = True
            continue

        if ch == '"':
            in_str = not in_str
            cur.append(ch)
            continue

        if ch == "+" and not in_str:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)

    parts.append("".join(cur).strip())
    return parts


def _eval_puro(expr: str) -> Any:
    # Ambiente seguro (sem builtins)
    env = {
        "verdadeiro": True,
        "falso": False,
        "True": True,
        "False": False,
        # Funções Portuino
        "ler": ler,
        "medir_distancia": medir_distancia,
        # Funções úteis (educacional)
        "int": int,
        "float": float,
        "str": str,
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
    }
    return eval(expr, {"__builtins__": {}}, {**env, **variaveis})


def avaliar_expressao(expr: str) -> Any:
    expr = expr.strip()

    # Troca palavras booleanas do Portuino para Python (também aceitamos verdadeiro/falso direto no env)
    expr = expr.replace("VERDADEIRO", "verdadeiro").replace("FALSO", "falso")

    # Concat amigável: "texto" + numero
    # Se houver aspas, tratamos '+' como concatenação por string
    if '"' in expr and "+" in expr:
        parts = _split_plus_outside_quotes(expr)
        vals = []
        for p in parts:
            v = _eval_puro(p)
            vals.append(str(v))
        return "".join(vals)

    # Caso geral
    try:
        return _eval_puro(expr)
    except NameError:
        # Se for só um nome de variável
        return variaveis.get(expr, expr)
    except Exception:
        # Retorna literal bruto (para não quebrar didática)
        return variaveis.get(expr, expr)


# ===============================
# Parser/Executor de blocos
# ===============================

def _extrair_bloco(linhas: List[str], i: int, fim_token: str) -> Tuple[List[str], int]:
    bloco = []
    i += 1
    while i < len(linhas) and linhas[i].strip() != fim_token:
        bloco.append(linhas[i])
        i += 1
    return bloco, i  # i aponta para o fim_token


def interpretar_linha(linha: str) -> None:
    linha = linha.strip()

    if not linha or linha.startswith("//"):
        return

    # declaração/atribuição: (inteiro|real|logico|texto)? var <- expr
    m = re.match(r"^(inteiro|real|logico|texto)?\s*(\w+)\s*<-\s*(.+)$", linha)
    if m:
        _tipo, nome, valor = m.groups()
        variaveis[nome] = avaliar_expressao(valor)
        return

    # escrever(...)
    if linha.startswith("escrever("):
        conteudo = re.findall(r"^escrever\((.*)\)$", linha)[0]
        print(avaliar_expressao(conteudo))
        return

    # esperar(ms)
    if linha.startswith("esperar("):
        ms = int(avaliar_expressao(re.findall(r"^esperar\((.*)\)$", linha)[0]))
        time.sleep(ms / 1000.0)
        return

    # configurar_saida(pino)
    if linha.startswith("configurar_saida("):
        pino = int(avaliar_expressao(re.findall(r"^configurar_saida\((.*)\)$", linha)[0]))
        configurar_saida(pino)
        return

    # configurar_entrada(pino)
    if linha.startswith("configurar_entrada("):
        pino = int(avaliar_expressao(re.findall(r"^configurar_entrada\((.*)\)$", linha)[0]))
        configurar_entrada(pino)
        return

    # ligar(pino)
    if linha.startswith("ligar("):
        pino = int(avaliar_expressao(re.findall(r"^ligar\((.*)\)$", linha)[0]))
        ligar(pino)
        return

    # desligar(pino)
    if linha.startswith("desligar("):
        pino = int(avaliar_expressao(re.findall(r"^desligar\((.*)\)$", linha)[0]))
        desligar(pino)
        return

    # ler(pino) como comando (imprime e guarda em _ultimo_ler)
    if linha.startswith("ler(") and linha.endswith(")"):
        pino = int(avaliar_expressao(re.findall(r"^ler\((.*)\)$", linha)[0]))
        v = ler(pino)
        variaveis["_ultimo_ler"] = v
        print(f"[LER] PIN {pino} = {v} ({ARD.modo})")
        return

    # Qualquer outra linha: tentamos avaliar como expressão (para não quebrar aulas)
    _ = avaliar_expressao(linha)


def interpretar_bloco(linhas: List[str]) -> None:
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if not linha or linha.startswith("//"):
            i += 1
            continue

        # se (...) entao
        if linha.startswith("se"):
            cond = re.findall(r"^se\s*\((.*)\)\s*entao$", linha)[0]
            bloco_se = []
            bloco_senao = []

            i += 1
            em_senao = False
            while i < len(linhas) and linhas[i].strip() != "fim_se":
                if linhas[i].strip() == "senao":
                    em_senao = True
                else:
                    (bloco_senao if em_senao else bloco_se).append(linhas[i])
                i += 1

            if bool(avaliar_expressao(cond)):
                interpretar_bloco(bloco_se)
            else:
                interpretar_bloco(bloco_senao)

            i += 1  # pula fim_se
            continue

        # enquanto (...) faca
        if linha.startswith("enquanto"):
            cond = re.findall(r"^enquanto\s*\((.*)\)\s*faca$", linha)[0]
            bloco, fim_i = _extrair_bloco(linhas, i, "fim_enquanto")
            while bool(avaliar_expressao(cond)):
                interpretar_bloco(bloco)
            i = fim_i + 1
            continue

        # para i de A ate B passo P
        if linha.startswith("para"):
            m = re.match(r"^para\s+(\w+)\s+de\s+(.*)\s+ate\s+(.*)\s+passo\s+(.*)$", linha)
            if not m:
                raise ValueError(f"Sintaxe inválida em PARA: {linha}")
            var, inicio, fim, passo = m.groups()
            bloco, fim_i = _extrair_bloco(linhas, i, "fim_para")

            inicio_val = int(avaliar_expressao(inicio))
            fim_val = int(avaliar_expressao(fim))
            passo_val = int(avaliar_expressao(passo))
            if passo_val == 0:
                raise ValueError("PASSO não pode ser 0.")

            # Inclusivo (estilo Visualg): até B inclusive
            if passo_val > 0:
                rng = range(inicio_val, fim_val + 1, passo_val)
            else:
                rng = range(inicio_val, fim_val - 1, passo_val)

            for v in rng:
                variaveis[var] = v
                interpretar_bloco(bloco)

            i = fim_i + 1
            continue

        # linha comum
        interpretar_linha(linha)
        i += 1


def interpretar_codigo(codigo: str) -> None:
    """
    Executa um programa Portuino dentro de:
      inicio ... fim
    """
    if ARD.modo == "REAL":
        _log_info(f"[INFO] Arduino REAL conectado em {ARD.porta}")
    else:
        _log_info("[WARN] Arduino não detectado (ou PyFirmata indisponível). Rodando em SIMULAÇÃO.")

    linhas = codigo.splitlines()

    em_execucao = False
    bloco = []
    for ln in linhas:
        s = ln.strip()
        if s == "inicio":
            em_execucao = True
            continue
        if s == "fim":
            break
        if em_execucao:
            bloco.append(ln)

    interpretar_bloco(bloco)
