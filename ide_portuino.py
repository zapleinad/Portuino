import os
import json
import threading
import textwrap
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_PATH = os.path.join(BASE_DIR, "manual_portuino.md")
MANUAL_VERSAO = "1.0"
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, Toplevel

from PIL import Image, ImageTk

from portuino_compiler import (
    ensure_arduino_cli,
    auto_detect_port_and_fqbn,
    compile_sketch,
    upload_sketch,
    list_ports_cli,
    BuildConfig,
)

APP_TITLE = "Portuino IDE"
DEFAULT_FQBN = "arduino:avr:uno"
DEFAULT_BAUD = 9600
CONFIG_FILE = "config_portuino.json"

def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)
def carregar_icone(nome, size=(24, 24)):
    # tenta "icones" (seu repo) e também "icons" (fallback)
    for pasta in ("icones", "icons"):
        path = resource_path(pasta, nome)
        if os.path.exists(path):
            img = Image.open(path).resize(size)
            return ImageTk.PhotoImage(img)
    return None


def listar_portas_pyserial():
    # Alternativa simples e confiável para listar COMs
    try:
        import serial.tools.list_ports

        return [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        return []


def manual_portuino_md() -> str:
    manual = textwrap.dedent(
        """
    # Portuino — Manual de Referência (v__VERSAO__)

    > Linguagem educacional em português (inspirada no Visualg) para ensinar programação e eletrônica com Arduino.

    ## Sumário
    - 1. Visão geral
    - 2. Instalação e requisitos
    - 3. Fluxo de uso na Portuino IDE
    - 4. Estrutura do programa
    - 5. Léxico e comentários
    - 6. Tipos e variáveis
    - 7. Expressões e operadores
    - 8. Controle de fluxo
    - 9. Biblioteca padrão (Arduino)
    - 10. Mapeamento para Arduino C++
    - 11. Exemplos oficiais
    - 12. Erros comuns
    - 13. Gramática (EBNF simplificada)

    ---
    ## 1) Visão geral

    O **Portuino** é uma linguagem em português voltada para **educação**.

    A Portuino IDE suporta dois caminhos:

    **(A) Verificar/Compilar + Enviar (Upload) (recomendado)**  
    - Traduz Portuino → Arduino C++ (`.ino`)  
    - Compila e envia para a placa via `arduino-cli`

    **(B) Modo interpretado (Firmata/PyFirmata)**  
    - Útil para testes rápidos e aulas  
    - Pode ter limitações em leituras baseadas em tempo (ex.: ultrassom)

    ---
    ## 2) Instalação e requisitos (Windows)

    **Python 3.10**
    ```powershell
    py -3.10 ide_portuino.py
    ```

    **Arduino CLI**
    ```powershell
    arduino-cli version
    arduino-cli config init
    arduino-cli core update-index
    arduino-cli core install arduino:avr
    ```

    ---
    ## 3) Fluxo na Portuino IDE

    1. Conecte o Arduino via USB  
    2. **Ferramentas > Porta**: selecione a COM correta  
    3. **Ferramentas > Placa**: selecione o FQBN (ex.: `arduino:avr:uno`)  
    4. **Sketch > Verificar/Compilar**  
    5. **Sketch > Enviar (Upload)**  
    6. **Ferramentas > Monitor Serial** para ver mensagens

    ---
    ## 4) Estrutura do programa

    ```portuino
    inicio
        escrever("Olá Portuino!")
    fim
    ```

    ---
    ## 5) Léxico e comentários

    Comentários:
    ```portuino
    // comentário de linha
    escrever("ok") // comentário ao lado
    ```

    Literais:
    - inteiro: 10, -2
    - real: 3.14
    - texto: "Olá"
    - lógico: verdadeiro, falso

    ---
    ## 6) Tipos e variáveis

    Tipos:
    - inteiro, real, logico, texto

    ```portuino
    inicio
        inteiro x <- 10
        real pi <- 3.14
        texto nome <- "Ana"
        logico ok <- verdadeiro

        x <- x + 1
    fim
    ```

    ---
    ## 7) Expressões e operadores

    Aritméticos: + - * /  
    Comparação: == != > < >= <=

    Concatenação:
    ```portuino
    inteiro x <- 7
    escrever("Valor: " + x)
    ```

    ---
    ## 8) Controle de fluxo

    **SE / SENAO**
    ```portuino
    se (x > 5) entao
        escrever("Maior")
    senao
        escrever("Menor/Igual")
    fim_se
    ```

    **ENQUANTO**
    ```portuino
    enquanto (verdadeiro) faca
        escrever("Loop")
        esperar(500)
    fim_enquanto
    ```

    **PARA**
    ```portuino
    para i de 1 ate 10 passo 1
        escrever("i=" + i)
    fim_para
    ```

    ---
    ## 9) Biblioteca padrão (Arduino)

    - esperar(ms)
    - escrever(x)
    - configurar_saida(pino)
    - configurar_entrada(pino)
    - ligar(pino) / desligar(pino)
    - ler(pino)
    - medir_distancia(trig, echo)

    ---
    ## 10) Mapeamento para Arduino C++

    - configurar_saida(p) → pinMode(p, OUTPUT);
    - configurar_entrada(p) → pinMode(p, INPUT);
    - ligar(p) → digitalWrite(p, HIGH);
    - desligar(p) → digitalWrite(p, LOW);
    - esperar(ms) → delay(ms);
    - escrever(x) → Serial.println(x);

    ---
    ## 11) Exemplos oficiais

    **Piscar LED**
    ```portuino
    inicio
        inteiro led <- 13
        configurar_saida(led)

        para i de 1 ate 5 passo 1
            ligar(led)
            esperar(500)
            desligar(led)
            esperar(500)
        fim_para
    fim
    ```

    **Botão liga LED**
    ```portuino
    inicio
        inteiro led <- 13
        inteiro botao <- 2

        configurar_saida(led)
        configurar_entrada(botao)

        enquanto (verdadeiro) faca
            se (ler(botao) == 1) entao
                ligar(led)
            senao
                desligar(led)
            fim_se
            esperar(50)
        fim_enquanto
    fim
    ```

    ---
    ## 12) Erros comuns

    - “Porta não definida”: selecione em Ferramentas > Porta
    - “arduino-cli não encontrado”: rode `arduino-cli version`

    ---
    ## 13) Gramática (EBNF simplificada)

    ```ebnf
    programa     = "inicio", { comando }, "fim" ;

    comando      = declaracao | atribuicao | escrever | esperar | gpio
                | se | enquanto | para ;

    declaracao   = tipo, id, "<-", expr ;
    atribuicao   = id, "<-", expr ;

    tipo         = "inteiro" | "real" | "logico" | "texto" ;

    se           = "se", "(", expr, ")", "entao",
                   { comando },
                   [ "senao", { comando } ],
                   "fim_se" ;

    enquanto     = "enquanto", "(", expr, ")", "faca",
                   { comando },
                   "fim_enquanto" ;

    para         = "para", id,
                   "de", expr, "ate", expr, "passo", expr,
                   { comando },
                   "fim_para" ;
    ```
    """
    ).strip()

    return manual.replace("__VERSAO__", MANUAL_VERSAO)


class PortuinoIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1100x750")

        self.current_file = None
        self.cfg = None  # BuildConfig

        self.config = self._carregar_config()

        self._theme()
        self._build_ui()
        self._bind_shortcuts()

        self._load_default_template()
        self._auto_detect_board_port()

    def _regerar_manual(self, widget_text):
        try:
            with open(MANUAL_PATH, "w", encoding="utf-8", newline="\n") as f:
                f.write(manual_portuino_md())
            with open(MANUAL_PATH, "r", encoding="utf-8") as f:
                conteudo = f.read()

            widget_text.config(state="normal")
            widget_text.delete("1.0", tk.END)
            widget_text.insert(tk.END, conteudo)
            widget_text.config(state="disabled")
            self.set_status("Manual regenerado com sucesso.")
        except Exception as e:
            messagebox.showerror("Manual", f"Falha ao regenerar manual:\n{e}")

    def open_manual(self):
        # Sempre garante o manual completo no disco (auto-gerado)
        try:
            if (not os.path.exists(MANUAL_PATH)) or (os.path.getsize(MANUAL_PATH) < 50):
                with open(MANUAL_PATH, "w", encoding="utf-8", newline="\n") as f:
                    f.write(manual_portuino_md())

            with open(MANUAL_PATH, "r", encoding="utf-8") as f:
                conteudo = f.read()

        except Exception as e:
            messagebox.showerror("Manual", f"Não foi possível criar/ler o manual:\n{e}")
            return

        # Janela do manual
        win = Toplevel(self.root)
        win.title("Manual do Portuino")
        win.geometry("950x700")

        top = tk.Frame(win)
        top.pack(fill="x", padx=8, pady=6)

        tk.Label(top, text="Buscar:").pack(side=tk.LEFT)
        busca = ttk.Entry(top)
        busca.pack(side=tk.LEFT, fill="x", expand=True, padx=8)

        def achar_proximo(event=None):
            termo = busca.get().strip()
            if not termo:
                return
            t.tag_remove("busca", "1.0", tk.END)
            pos = t.search(termo, t.index(tk.INSERT), stopindex=tk.END, nocase=True)
            if not pos:
                pos = t.search(termo, "1.0", stopindex=tk.END, nocase=True)
            if pos:
                fim = f"{pos}+{len(termo)}c"
                t.tag_add("busca", pos, fim)
                t.tag_config("busca", background="#FFF59D")  # amarelo claro
                t.mark_set(tk.INSERT, fim)
                t.see(pos)

        ttk.Button(top, text="Encontrar", command=achar_proximo).pack(side=tk.LEFT)
        ttk.Button(
            top, text="Regerar manual", command=lambda: self._regerar_manual(t)
        ).pack(side=tk.RIGHT)

        t = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI", 11))
        t.pack(fill="both", expand=True, padx=8, pady=6)
        t.insert(tk.END, conteudo)
        t.config(state="disabled")

        busca.bind("<Return>", achar_proximo)

    # ---------------- Config ----------------
    def _carregar_config(self):
        cfg = {
            "default_fqbn": DEFAULT_FQBN,
            "default_baud": DEFAULT_BAUD,
            "icon_size": 24,
            "editor_font_family": "Consolas",
            "editor_font_size": 12,
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg.update(json.load(f))
            except Exception:
                pass
        return cfg

    def _salvar_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Preferências", f"Falha ao salvar configurações: {e}")

    # ---------------- UI ----------------
    def _theme(self):
        self.style = ttk.Style(self.root)
        self.root.tk_setPalette(background="#ffffff")
        self.style.theme_use("default")

    def _build_ui(self):
        # Menu
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self._menu_arquivo()
        self._menu_editar()
        self._menu_sketch()
        self._menu_ferramentas()
        self._menu_ajuda()

        # Barra de ferramentas (toolbar)
        self.toolbar = tk.Frame(self.root, bg="#0B6E75")  # Arduino-ish
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        icon_px = int(self.config.get("icon_size", 24))
        TAM = (icon_px, icon_px)

        def try_icon(name):
            try:
                return carregar_icone(name, TAM)
            except Exception:
                return None

        self.ico_novo = try_icon("novo.png")
        self.ico_abrir = try_icon("abrir.png")
        self.ico_salvar = try_icon("salvar.png")
        self.ico_verificar = try_icon("verificar.png")
        self.ico_upload = try_icon("upload.png")

        self._btn(self.ico_novo, self.new_file, "Novo").pack(
            side=tk.LEFT, padx=2, pady=2
        )
        self._btn(self.ico_abrir, self.open_file, "Abrir").pack(
            side=tk.LEFT, padx=2, pady=2
        )
        self._btn(self.ico_salvar, self.save_file, "Salvar").pack(
            side=tk.LEFT, padx=2, pady=2
        )

        tk.Frame(self.toolbar, width=16, bg="#0B6E75").pack(side=tk.LEFT)

        self._btn(self.ico_verificar, self.verify_compile, "Verificar/Compilar").pack(
            side=tk.LEFT, padx=2, pady=2
        )
        self._btn(self.ico_upload, self.upload, "Enviar (Upload)").pack(
            side=tk.LEFT, padx=2, pady=2
        )

        # Info placa/porta
        self.info = tk.Label(
            self.toolbar, text="Placa: ? | Porta: ?", bg="#0B6E75", fg="white"
        )
        self.info.pack(side=tk.RIGHT, padx=10)

        # Editor + Console (split)
        self.paned = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        self.paned.pack(fill="both", expand=True, padx=8, pady=6)

        self.editor_frame = ttk.LabelFrame(self.paned, text="Editor Portuino")
        font_family = self.config.get("editor_font_family", "Consolas")
        font_size = int(self.config.get("editor_font_size", 12))
        self.editor = scrolledtext.ScrolledText(
            self.editor_frame, font=(font_family, font_size), wrap=tk.WORD, undo=True
        )
        self.editor.pack(fill="both", expand=True)
        self.paned.add(self.editor_frame, weight=4)

        self.console_frame = ttk.LabelFrame(self.paned, text="Saída / Console")
        self.console = scrolledtext.ScrolledText(
            self.console_frame, height=10, font=("Consolas", 10), state="disabled"
        )
        self.console.pack(fill="both", expand=True)
        self.paned.add(self.console_frame, weight=1)

        # Status bar
        self.status = tk.Label(
            self.root,
            text="Pronto.",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#0B6E75",
            fg="white",
        )
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _btn(self, icon, cmd, tooltip):
        b = tk.Button(
            self.toolbar,
            image=icon,
            command=cmd,
            bg="#0B6E75",
            activebackground="#0B6E75",
            bd=0,
        )
        b._tooltip = tooltip
        return b

    # ---------------- Menus ----------------
    def _menu_arquivo(self):
        m = tk.Menu(self.menu, tearoff=0)
        m.add_command(label="Novo", accelerator="Ctrl+N", command=self.new_file)
        m.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.open_file)
        m.add_separator()
        m.add_command(label="Salvar", accelerator="Ctrl+S", command=self.save_file)
        m.add_command(
            label="Salvar como...",
            accelerator="Ctrl+Shift+S",
            command=self.save_as_file,
        )
        m.add_separator()
        m.add_command(label="Sair", accelerator="Ctrl+Q", command=self.root.quit)
        self.menu.add_cascade(label="Arquivo", menu=m)

    def _menu_editar(self):
        m = tk.Menu(self.menu, tearoff=0)
        m.add_command(
            label="Desfazer",
            accelerator="Ctrl+Z",
            command=lambda: self.editor.event_generate("<<Undo>>"),
        )
        m.add_command(
            label="Refazer",
            accelerator="Ctrl+Y",
            command=lambda: self.editor.event_generate("<<Redo>>"),
        )
        m.add_separator()
        m.add_command(
            label="Recortar",
            accelerator="Ctrl+X",
            command=lambda: self.editor.event_generate("<<Cut>>"),
        )
        m.add_command(
            label="Copiar",
            accelerator="Ctrl+C",
            command=lambda: self.editor.event_generate("<<Copy>>"),
        )
        m.add_command(
            label="Colar",
            accelerator="Ctrl+V",
            command=lambda: self.editor.event_generate("<<Paste>>"),
        )
        m.add_command(
            label="Selecionar tudo",
            accelerator="Ctrl+A",
            command=lambda: self.editor.tag_add("sel", "1.0", "end"),
        )
        m.add_separator()
        m.add_command(
            label="Auto formatar", accelerator="Ctrl+T", command=self.auto_formatar
        )
        self.menu.add_cascade(label="Editar", menu=m)

    def _menu_sketch(self):
        m = tk.Menu(self.menu, tearoff=0)
        m.add_command(
            label="Verificar/Compilar",
            accelerator="Ctrl+R",
            command=self.verify_compile,
        )
        m.add_command(
            label="Enviar (Upload)", accelerator="Ctrl+U", command=self.upload
        )
        self.menu.add_cascade(label="Sketch", menu=m)

    def _menu_ferramentas(self):
        m = tk.Menu(self.menu, tearoff=0)

        m.add_command(
            label="Monitor Serial",
            accelerator="Ctrl+Shift+M",
            command=self.serial_monitor,
        )
        m.add_separator()

        # Submenu Placa
        self.menu_placa = tk.Menu(m, tearoff=0)
        self.menu_placa.add_command(
            label="Selecionar...", command=self.selecionar_placa_busca
        )
        self.menu_placa.add_command(
            label="Detectar automaticamente", command=self._auto_detect_board_port
        )
        m.add_cascade(label="Placa", menu=self.menu_placa)

        # Submenu Porta (dinâmico)
        self.menu_porta = tk.Menu(m, tearoff=0)
        self.menu_porta.add_command(
            label="Atualizar lista de portas", command=self.atualizar_menu_portas
        )
        m.add_cascade(label="Porta", menu=self.menu_porta)

        m.add_separator()
        m.add_command(label="Preferências...", command=self.preferencias)
        m.add_command(
            label="Listar placas/portas (arduino-cli)", command=self.show_board_list
        )

        self.menu.add_cascade(label="Ferramentas", menu=m)

        # popular portas ao abrir
        self.atualizar_menu_portas()

    def _menu_ajuda(self):
        m = tk.Menu(self.menu, tearoff=0)
        m.add_command(label="Manual do Portuino", command=self.open_manual)
        m.add_separator()
        m.add_command(
            label="Sobre a Portuino IDE",
            command=lambda: messagebox.showinfo(
                "Sobre",
                "Portuino IDE\nInterface em português inspirada na Arduino IDE.\n",
            ),
        )
        self.menu.add_cascade(label="Ajuda", menu=m)

    # ------------- Util -------------
    def log(self, txt: str):
        self.console.config(state="normal")
        self.console.insert(tk.END, txt + "\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def set_status(self, txt: str):
        self.status.config(text=txt)

    # ---------------- Placa / Porta ----------------
    def _auto_detect_board_port(self):
        try:
            ensure_arduino_cli()
            prefer = self.config.get("default_fqbn", DEFAULT_FQBN)
            cfg = auto_detect_port_and_fqbn(prefer_fqbn=prefer)
            cfg.baud = int(self.config.get("default_baud", DEFAULT_BAUD))
            self.cfg = cfg
            self.info.config(text=f"Placa: {cfg.fqbn} | Porta: {cfg.port}")
            self.set_status("Placa/porta detectadas.")
        except Exception as e:
            self.set_status("Falha ao detectar placa/porta.")
            messagebox.showerror("Detecção", str(e))

    def atualizar_menu_portas(self):
        self.menu_porta.delete(0, tk.END)

        portas = listar_portas_pyserial()
        if not portas:
            self.menu_porta.add_command(
                label="(nenhuma porta encontrada)", state="disabled"
            )
        else:
            for p in portas:
                self.menu_porta.add_command(
                    label=p, command=lambda porta=p: self.definir_porta(porta)
                )

        self.menu_porta.add_separator()
        self.menu_porta.add_command(
            label="Atualizar lista de portas", command=self.atualizar_menu_portas
        )

    def definir_porta(self, porta: str):
        if not self.cfg:
            self.cfg = BuildConfig(
                fqbn=self.config.get("default_fqbn", DEFAULT_FQBN),
                port=porta,
                baud=int(self.config.get("default_baud", DEFAULT_BAUD)),
            )
        else:
            self.cfg.port = porta
        self.info.config(text=f"Placa: {self.cfg.fqbn} | Porta: {self.cfg.port}")
        self.set_status(f"Porta selecionada: {porta}")

    def selecionar_placa_busca(self):
        # Janela com busca + lista de FQBN via arduino-cli
        win = Toplevel(self.root)
        win.title("Selecionar placa (FQBN)")
        win.geometry("800x520")

        top = tk.Frame(win)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Buscar:").pack(side=tk.LEFT)
        busca = ttk.Entry(top)
        busca.pack(side=tk.LEFT, fill="x", expand=True, padx=8)

        lst = tk.Listbox(win)
        lst.pack(fill="both", expand=True, padx=10, pady=8)

        info = tk.Label(win, text="Carregando placas via arduino-cli...", anchor="w")
        info.pack(fill="x", padx=10, pady=(0, 8))

        boards = []

        def carregar():
            nonlocal boards
            try:
                ensure_arduino_cli()
                # Usamos board listall (lista grande, mas completa)
                import subprocess

                p = subprocess.run(
                    ["arduino-cli", "board", "listall"], capture_output=True, text=True
                )
                out = (p.stdout or "") + (p.stderr or "")
                if p.returncode != 0:
                    raise RuntimeError(out)

                # tenta extrair FQBN: padrão: "NAME  FQBN"
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
                # pula cabeçalhos se existirem
                # vamos pegar tudo que parece "algo:algo:algo"
                fqbn = []
                for ln in lines:
                    m = __import__("re").search(
                        r"\b([a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+)\b", ln
                    )
                    if m:
                        fqbn.append((ln, m.group(1)))
                boards = fqbn

                def refresh(filter_text=""):
                    lst.delete(0, tk.END)
                    ft = filter_text.lower().strip()
                    for label, f in boards:
                        if not ft or ft in label.lower() or ft in f.lower():
                            lst.insert(tk.END, f"  {f}   |   {label}")

                def on_change(_=None):
                    refresh(busca.get())

                busca.bind("<KeyRelease>", on_change)
                refresh("")
                info.config(
                    text=f"{len(boards)} placas encontradas. Selecione uma e clique em Aplicar."
                )

            except Exception as e:
                info.config(text="Falha ao listar placas.")
                messagebox.showerror("Placa", f"Erro ao listar placas:\n{e}")

        def aplicar():
            sel = lst.curselection()
            if not sel:
                return
            item = lst.get(sel[0])
            # item começa com "FQBN | ..."
            fqbn = item.split("|")[0].strip()
            if not self.cfg:
                self.cfg = BuildConfig(
                    fqbn=fqbn,
                    port="?",
                    baud=int(self.config.get("default_baud", DEFAULT_BAUD)),
                )
            else:
                self.cfg.fqbn = fqbn
            self.info.config(text=f"Placa: {self.cfg.fqbn} | Porta: {self.cfg.port}")
            self.set_status(f"Placa selecionada: {fqbn}")
            win.destroy()

        btns = tk.Frame(win)
        btns.pack(fill="x", padx=10, pady=8)
        ttk.Button(btns, text="Aplicar", command=aplicar).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Fechar", command=win.destroy).pack(side=tk.RIGHT, padx=8)

        threading.Thread(target=carregar, daemon=True).start()

    # ---------------- Preferências ----------------
    def preferencias(self):
        win = Toplevel(self.root)
        win.title("Preferências")
        win.geometry("520x320")

        frm = tk.Frame(win)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        def row(label, widget):
            r = tk.Frame(frm)
            r.pack(fill="x", pady=6)
            tk.Label(r, text=label, width=18, anchor="w").pack(side=tk.LEFT)
            widget.pack(side=tk.LEFT, fill="x", expand=True)
            return widget

        fqbn_var = tk.StringVar(value=self.config.get("default_fqbn", DEFAULT_FQBN))
        baud_var = tk.StringVar(
            value=str(self.config.get("default_baud", DEFAULT_BAUD))
        )
        icon_var = tk.StringVar(value=str(self.config.get("icon_size", 24)))
        font_var = tk.StringVar(value=self.config.get("editor_font_family", "Consolas"))
        fontsize_var = tk.StringVar(value=str(self.config.get("editor_font_size", 12)))

        row("FQBN padrão:", ttk.Entry(frm, textvariable=fqbn_var))
        row("Baud padrão:", ttk.Entry(frm, textvariable=baud_var))
        row("Tamanho ícone:", ttk.Entry(frm, textvariable=icon_var))
        row("Fonte editor:", ttk.Entry(frm, textvariable=font_var))
        row("Tam. fonte:", ttk.Entry(frm, textvariable=fontsize_var))

        def salvar():
            try:
                self.config["default_fqbn"] = fqbn_var.get().strip() or DEFAULT_FQBN
                self.config["default_baud"] = int(baud_var.get().strip())
                self.config["icon_size"] = int(icon_var.get().strip())
                self.config["editor_font_family"] = font_var.get().strip() or "Consolas"
                self.config["editor_font_size"] = int(fontsize_var.get().strip())

                self._salvar_config()
                messagebox.showinfo(
                    "Preferências",
                    "Preferências salvas.\n(Reabra a IDE para aplicar ícones/fonte).",
                )
                win.destroy()
            except Exception as e:
                messagebox.showerror("Preferências", f"Valores inválidos: {e}")

        b = tk.Frame(win)
        b.pack(fill="x", padx=12, pady=12)
        ttk.Button(b, text="Salvar", command=salvar).pack(side=tk.RIGHT)
        ttk.Button(b, text="Cancelar", command=win.destroy).pack(side=tk.RIGHT, padx=8)

    # ---------------- Ações básicas ----------------
    def show_board_list(self):
        try:
            ensure_arduino_cli()
            out = list_ports_cli()
            messagebox.showinfo("Placas/Portas", out)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def new_file(self):
        self.current_file = None
        self.editor.delete("1.0", tk.END)  # limpa tudo
        self.editor.edit_reset()  # limpa histórico de desfazer/refazer
        self.set_status("Novo sketch (em branco).")

    def open_file(self):
        p = filedialog.askopenfilename(
            filetypes=[("Portuino", "*.ptn"), ("Todos os arquivos", "*.*")]
        )
        if not p:
            return
        with open(p, "r", encoding="utf-8") as f:
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, f.read())
        self.current_file = p
        self.set_status(f"Aberto: {os.path.basename(p)}")

    def save_file(self):
        if not self.current_file:
            return self.save_as_file()
        with open(self.current_file, "w", encoding="utf-8") as f:
            f.write(self.editor.get("1.0", tk.END))
        self.set_status(f"Salvo: {os.path.basename(self.current_file)}")

    def save_as_file(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".ptn", filetypes=[("Portuino", "*.ptn")]
        )
        if not p:
            return
        self.current_file = p
        self.save_file()

    def auto_formatar(self):
        """
        Formatador simples (estilo didático): ajusta indentação por blocos.
        """
        code = self.editor.get("1.0", tk.END).splitlines()
        out = []
        indent = 0

        def is_close(s):
            return s in ("fim_se", "fim_enquanto", "fim_para", "fim")

        def is_open(s):
            return (
                (s.startswith("se ") and s.endswith(" entao"))
                or s.startswith("enquanto ")
                or s.startswith("para ")
                or s == "inicio"
                or s == "senao"
            )

        for ln in code:
            s = ln.strip()
            if not s:
                out.append("")
                continue

            if is_close(s):
                indent = max(0, indent - 1)

            if s == "senao":
                indent = max(0, indent - 1)
                out.append("    " * indent + s)
                indent += 1
                continue

            out.append("    " * indent + s)

            if is_open(s) and s != "senao":
                indent += 1

        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, "\n".join(out).rstrip() + "\n")
        self.set_status("Auto formatação aplicada.")

    def verify_compile(self):
        def work():
            try:
                self.set_status("Verificando/compilando...")
                self.log("== Verificar/Compilar ==")

                if not self.cfg:
                    self._auto_detect_board_port()

                # aplica defaults se faltarem
                if self.cfg:
                    if not getattr(self.cfg, "fqbn", None) or self.cfg.fqbn == "?":
                        self.cfg.fqbn = self.config.get("default_fqbn", DEFAULT_FQBN)
                    self.cfg.baud = int(self.config.get("default_baud", DEFAULT_BAUD))

                code = self.editor.get("1.0", tk.END)
                _, out = compile_sketch(code, self.cfg)
                self.log(out.strip())
                self.set_status("Compilação OK.")
            except Exception as e:
                self.log(str(e))
                self.set_status("Erro na compilação.")

        threading.Thread(target=work, daemon=True).start()

    def upload(self):
        def work():
            try:
                self.set_status("Enviando para a placa (upload)...")
                self.log("== Enviar (Upload) ==")

                if not self.cfg:
                    self._auto_detect_board_port()

                if self.cfg and (not self.cfg.port or self.cfg.port == "?"):
                    raise RuntimeError(
                        "Porta não definida. Vá em Ferramentas > Porta e selecione a COM correta."
                    )

                # aplica defaults
                if self.cfg:
                    if not getattr(self.cfg, "fqbn", None) or self.cfg.fqbn == "?":
                        self.cfg.fqbn = self.config.get("default_fqbn", DEFAULT_FQBN)
                    self.cfg.baud = int(self.config.get("default_baud", DEFAULT_BAUD))

                code = self.editor.get("1.0", tk.END)
                out = upload_sketch(code, self.cfg)
                self.log(out.strip())
                self.set_status("Upload concluído.")
            except Exception as e:
                self.log(str(e))
                self.set_status("Erro no upload.")

        threading.Thread(target=work, daemon=True).start()

    def serial_monitor(self):
        try:
            import serial

            if not self.cfg or not self.cfg.port or self.cfg.port == "?":
                self._auto_detect_board_port()

            if not self.cfg or not self.cfg.port or self.cfg.port == "?":
                raise RuntimeError(
                    "Porta não definida. Selecione em Ferramentas > Porta."
                )

            win = Toplevel(self.root)
            win.title("Monitor Serial")
            win.geometry("800x450")

            text = scrolledtext.ScrolledText(win, font=("Consolas", 10))
            text.pack(fill="both", expand=True)

            entry = ttk.Entry(win)
            entry.pack(fill="x")

            ser = serial.Serial(self.cfg.port, self.cfg.baud, timeout=0.2)

            def reader():
                while True:
                    try:
                        data = ser.readline()
                        if data:
                            text.insert(tk.END, data.decode(errors="ignore"))
                            text.see(tk.END)
                    except:
                        break

            def send(_=None):
                msg = entry.get()
                entry.delete(0, tk.END)
                if msg:
                    ser.write((msg + "\n").encode())

            entry.bind("<Return>", send)
            threading.Thread(target=reader, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Monitor Serial", str(e))

    def open_manual(self):
        # Sempre garante o manual completo no disco (auto-gerado)
        try:
            if (not os.path.exists(MANUAL_PATH)) or (os.path.getsize(MANUAL_PATH) < 50):
                with open(MANUAL_PATH, "w", encoding="utf-8", newline="\n") as f:
                    f.write(manual_portuino_md())

            with open(MANUAL_PATH, "r", encoding="utf-8") as f:
                conteudo = f.read()

        except Exception as e:
            messagebox.showerror("Manual", f"Não foi possível criar/ler o manual:\n{e}")
            return

        # Janela do manual
        win = Toplevel(self.root)
        win.title("Manual do Portuino")
        win.geometry("950x700")

        top = tk.Frame(win)
        top.pack(fill="x", padx=8, pady=6)

        tk.Label(top, text="Buscar:").pack(side=tk.LEFT)
        busca = ttk.Entry(top)
        busca.pack(side=tk.LEFT, fill="x", expand=True, padx=8)

        def achar_proximo(event=None):
            termo = busca.get().strip()
            if not termo:
                return
            t.tag_remove("busca", "1.0", tk.END)
            pos = t.search(termo, t.index(tk.INSERT), stopindex=tk.END, nocase=True)
            if not pos:
                pos = t.search(termo, "1.0", stopindex=tk.END, nocase=True)
            if pos:
                fim = f"{pos}+{len(termo)}c"
                t.tag_add("busca", pos, fim)
                t.tag_config("busca", background="#FFF59D")  # amarelo claro
                t.mark_set(tk.INSERT, fim)
                t.see(pos)

        ttk.Button(top, text="Encontrar", command=achar_proximo).pack(side=tk.LEFT)
        ttk.Button(
            top, text="Regerar manual", command=lambda: self._regerar_manual(t)
        ).pack(side=tk.RIGHT)

        t = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Segoe UI", 11))
        t.pack(fill="both", expand=True, padx=8, pady=6)
        t.insert(tk.END, conteudo)
        t.config(state="disabled")

        busca.bind("<Return>", achar_proximo)

    def _load_default_template(self):
        template = """inicio
    inteiro led <- 13
    configurar_saida(led)

    para i de 1 ate 5 passo 1
        ligar(led)
        esperar(500)
        desligar(led)
        esperar(500)
    fim_para

    escrever("Pronto!")
fim
"""
        self.editor.insert(tk.END, template)

    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-n>", lambda e: self.new_file())
        r.bind("<Control-o>", lambda e: self.open_file())
        r.bind("<Control-s>", lambda e: self.save_file())
        r.bind("<Control-S>", lambda e: self.save_as_file())
        r.bind("<Control-q>", lambda e: self.root.quit())
        r.bind("<Control-r>", lambda e: self.verify_compile())
        r.bind("<Control-u>", lambda e: self.upload())
        r.bind("<Control-t>", lambda e: self.auto_formatar())
        r.bind("<Control-Shift-M>", lambda e: self.serial_monitor())

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PortuinoIDE().run()

