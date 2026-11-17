# Notas para IA: desenvolvimento de apps para HP Prime

Este arquivo registra o que deu errado e o que funcionou no desenvolvimento do
**Visor** (visualizador de imagens e PDF para HP Prime). É para servir de
contexto a assistentes de IA que forem mexer neste projeto ou criar outros apps
para a HP Prime. Ambiente: **firmware 2.4.2 (2026-09-09)**, emulador oficial
*HP Prime Virtual Calculator* para Windows e uma HP Prime real. Cada item diz se
foi visto no emulador, na real ou nos dois.

---

## Arquitetura do projeto

| Arquivo | Papel |
|---|---|
| `visor_hp.py` | Conversor no PC (Python + Pillow + PyMuPDF). Gera a pasta `<Nome>.hpappdir`. |
| `Visor.hpppl` | Código-fonte HPPPL do app (texto). **A calculadora não lê esse arquivo diretamente.** |
| `Visor_compilado.hpappprgm` | O mesmo programa já compilado pela calculadora (binário). É ele que vai dentro do app. |
| `base_app.hpapp` | Estado do app base (Function), copiado de uma calculadora real. Vira `<Nome>.hpapp`. |
| `icon.png` | Ícone 38x38 do app, copiado para dentro do `.hpappdir`. |
| `converter.bat` | Atalho para arrastar arquivos e converter. |
| `ferramentas/*.ps1` | Scripts que controlam o emulador para testes automatizados (ver abaixo). |

Estrutura de um app gerado:

```
Visor.hpappdir/
  Visor.hpapp          <- base_app.hpapp
  Visor.hpappprgm      <- Visor_compilado.hpappprgm
  icon.png             <- ícone da biblioteca de apps
  p1_1_1_1.png ...     <- blocos: p<pagina>_<nivel>_<coluna>_<linha>.png
```

---

## O que deu errado (e por quê)

### 1. Atualizador do Connectivity Kit não baixa
O `update.xml` oficial (`ftp.hp.com/pub/calculators/Prime/update.xml`) aponta para
`www.moravia-parts.com/hp-prime/`, que responde **403**. Firmwares, Kit e emulador
estão em **https://www.hpcalc.org/prime/** (pasta `pc/`). Os instaladores são
assinados por *MORAVIA Consulting*, a desenvolvedora oficial.

### 2. `.hpappprgm` em texto puro chega VAZIO na firmware 2.4
Gerar o `.hpappprgm` como texto UTF-16LE (com ou sem BOM) **não funciona**: o
app aparece, mas o programa fica vazio (o editor mostra `<App>:Main(PPL)` sem
nada). O sintoma para o usuário é que o app abre a tela de fórmulas
(`F1(X)=...`) em vez de rodar.
A firmware 2.4 grava o `.hpappprgm` num **formato binário** (cabeçalho, bytecode
e o fonte UTF-16 embutido) que não dá para gerar no PC.
**Solução:** compilar uma vez no emulador e reaproveitar o binário (ver
"Fluxo para alterar o programa"). O binário não depende do nome do app: dá para
renomear o arquivo para `<OutroNome>.hpappprgm` e funciona.

### 3. Erro de sintaxe: mais de 8 variáveis num `LOCAL`
`LOCAL a1,a2,a3,a4,a5,a6,a7,a8,a9;` dá **"erro de sintaxe"**, e a mensagem não
diz a linha. **Máximo de 8 nomes por `LOCAL`**: divida em várias linhas.

### 4. Erro de sintaxe: `e` e `i` como nomes
`e` (constante de Euler) e `i` (unidade imaginária) são reservados. Usar como
parâmetro (`F(a,b,c,d,e)`) ou variável (`LOCAL i`) dá erro de sintaxe. Use
`j`, `k`, `u1`... Desconfie também de outros nomes de 1 letra que sejam
funções ou constantes.

### 5. Estouro de memória com imagens grandes
Uma imagem de 960x1358 carregada com `G1:=AFiles("x.png")` funciona no
emulador, mas **na calculadora real aborta o programa** (cerca de 5 MB como
GROB, 4 bytes por pixel). Até 640x906 funcionou. Quando o programa aborta
dentro de um app, a calculadora cai na vista do app base.
**Solução:** cortar em blocos de 480x360, carregar só os visíveis (no máximo
2x2) em 4 GROBs-cache (G3..G6, com LRU), liberar antes de recarregar
(`DIMGROB_P(Gx,1,1,0)`) e envolver o carregamento em `IFERR`.
**O emulador NÃO reproduz os limites de memória da calculadora real.**

### 6. Abrir o app pelo ícone não roda `START()`
`START()` só roda pelo botão **Início** da biblioteca de apps. Tocar no ícone
abre a vista Simbólica do app base.
**Solução:** definir também `Symb()` no programa do app, chamando a função
principal. Assim tocar no ícone abre direto.

### 7. Automação do emulador
- Copiar o `.hpappdir` para `Documentos\HP Prime\Calculators\Prime\` **com o
  emulador fechado** importa o app ao abrir (para arquivos `.png` e `.hpapp`; o
  `.hpappprgm` em texto é descartado, ver item 2).
- `SendKeys` com letras **não** chega ao emulador; dígitos às vezes sim.
  **Ctrl+V funciona** no editor de programas (cola o texto da área de
  transferência). O menu Editar → Colar não funcionou.
- O resto se faz com **cliques do mouse nas teclas da skin** (coordenadas em
  `ferramentas/seq.ps1`, para janela de 343x788).
- Fechar com `Stop-Process`/`taskkill /F` não salva o estado. O emulador
  recarrega a pasta ao abrir de novo.
- A janela pode abrir em coordenada negativa (segundo monitor): mova com
  `MoveWindow` antes de capturar. `PrintWindow` às vezes captura a janela
  errada; `CopyFromScreen` com a janela em primeiro plano foi mais confiável.

---

## O que funciona (validado)

- **Imagens no app:** arquivos PNG dentro do `.hpappdir` são lidos com
  `G3:=AFiles("nome.png")`, que retorna um GROB. `AFiles()` sem argumento
  retorna a lista de nomes de arquivos do app (usada com `POS(lista,nome)` para
  testar se um arquivo existe).
- **PNG RGB de 8 bits** gerado pelo Pillow (`optimize=True`) é aceito.
  Transparência foi achatada sobre fundo branco; não testamos PNG com paleta ou
  escala de cinza.
- **Ícone:** `icon.png` de 38x38 (RGBA) dentro do `.hpappdir` vira o ícone na
  biblioteca de apps.
- **Desenho sem flicker:** desenhar em `G2` (320x240) e terminar com
  `BLIT_P(G0,G2)`.
- **`BLIT_P` 1:1:** usar `BLIT_P(G2,dx1,dy1,dx2,dy2,Gsrc,sx1,sy1,sx2,sy2)` com
  origem e destino do mesmo tamanho. Redimensionar na calculadora é lento e
  feio (vizinho mais próximo). Por isso o PC já gera cada nível de zoom no
  tamanho exato, com Lanczos.
- **Teclado:** `WAIT(-1)` retorna o código da tecla, ou uma lista para toque.
  Códigos usados: cima 2, esquerda 7, direita 8, baixo 12, Esc 4, Enter 30,
  "9" 34, "3" 44, "−" 45, "+" 50.
- **Toque:** `WAIT(-1)` retorna `{tipo,x,y,...}`. Tipo 0 = dedo encostou,
  tipo 1 = movimento. Guardando a última posição dá para arrastar.
- **Número para texto:** `NumStr` manual (com `CHAR(48+d)`), para não depender
  do formato numérico configurado na calculadora (ex.: "1.00" em modo Fixo).
- **Texto na tela:** `TEXTOUT_P(texto,G2,x,y,1,cor)`, onde a fonte 1 é a pequena.
- **Sair limpo:** `STARTVIEW(-1,1)` volta para a tela Home ao fim de
  `START()`/`Symb()`.
- **Funções precisam ser definidas antes de serem usadas** no arquivo (ou
  declaradas antes).

---

## Fluxo para alterar o programa (`Visor.hpppl`)

1. Edite `Visor.hpppl`.
2. Gere um app de teste com o conversor e copie para
   `Documentos\HP Prime\Calculators\Prime\` com o emulador fechado.
3. Abra o emulador, deixe o app ativo, aperte **Shift + 1** (catálogo de
   programas), escolha `<App> (App)` e toque em **Editar**.
4. Limpe o editor (Shift + Esc → OK) e cole o código (Ctrl+V). Pode usar
   `ferramentas/pastecheck.ps1`, que limpa, cola e toca em **Verif.**
5. "Nenhum erro no programa" → copie
   `Documentos\HP Prime\Calculators\Prime\<App>.hpappdir\<App>.hpappprgm` para
   `Visor_compilado.hpappprgm`.
6. Gere o app de novo e teste. Se puder, **teste na calculadora real**, por
   causa da memória.

Ferramentas de teste (`ferramentas/`, PowerShell):
- `emu.ps1 shot|click|keys|drag`: captura e clica na janela do emulador.
- `pastecheck.ps1 <arquivo> <saida.png>`: cola o código no editor e verifica.
- `seq.ps1 "plus,down,three" <prefixo>`: aperta teclas e monta uma imagem com
  todas as telas.

---

## Pendências e ideias
- Não sabemos o limite exato de memória para GROBs na calculadora real. A
  versão com blocos (480x360, 4 em cache) foi testada no emulador, mas **ainda
  falta confirmar na calculadora real**. A versão anterior, com imagem inteira,
  funcionou na real até 640x906 e falhou em 960x1358.
- Não testamos o arquivo `Visor_compilado.hpappprgm` em firmwares mais antigas.
- Não testamos PNG em escala de cinza ou com paleta (geraria arquivos menores).
