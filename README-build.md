# PortuinoIDE — Build (Windows + Linux)

Este pacote contém:
- Workflow do GitHub Actions para gerar artefatos no Windows e no Linux
- Spec opcional do PyInstaller
- Observações para evitar erros comuns de "ModuleNotFoundError"

## Erro: "No module named 'portuino_compiler'"
Causa típica: PyInstaller não incluiu módulos locais.
Correção aplicada:
- Adicionar `--paths .`
- Forçar `--hidden-import portuino_compiler` e `--hidden-import interpretador_portuino`

## Arduino CLI (sem pré-instalação)
O arquivo `portuino_compiler.py` foi ajustado para:
1) procurar `arduino-cli` embutido no bundle (se você empacotar em tools/arduino-cli)
2) procurar no PATH
3) baixar automaticamente (1ª execução) do release "latest" do Arduino CLI

Isso remove a necessidade de instalar o CLI manualmente.
