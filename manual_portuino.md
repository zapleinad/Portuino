# Portuino — Manual de Referência (v1.0)

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