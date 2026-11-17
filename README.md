# Visor HP Prime

Visualizador de imagens e PDFs para a calculadora HP Prime (firmware 2.4). O conversor no PC transforma as páginas em blocos PNG já na resolução da tela, e o app na calculadora navega com as setas, dá zoom com + / − e troca de página com 3 / 9.

Requisitos no PC: Python 3 com `pip install pillow pymupdf`.

Notas técnicas e lições aprendidas: [NOTAS-PARA-IA.md](NOTAS-PARA-IA.md).

## 1. Converter os arquivos (no PC)

Arraste imagens (PNG, JPG, BMP, GIF, WEBP, TIFF) e/ou PDFs em cima de **converter.bat**.
Ou rode pelo terminal:

```
python visor_hp.py apostila.pdf foto.jpg -o saida
```

Opções:
- `--paginas 1-10,15`: escolhe as páginas dos PDFs
- `--zoom-max 2`: zoom máximo (1 a 4 vezes a largura da tela). Menos zoom gera arquivos menores.
- `--cinza`: converte tudo para tons de cinza
- `--nome Apostila`: nome do app (permite ter vários apps na calculadora, um por documento)

O resultado fica em `saida\Visor.hpappdir`. Cada página é renderizada em vários
níveis de zoom (página inteira, largura da tela, 1,5x, 2x, 3x), e cada nível é
cortado em blocos PNG de 480x360 (`p<página>_<nível>_<coluna>_<linha>.png`).
A calculadora carrega só os blocos visíveis, no máximo 4 por vez, para não
estourar a memória. O app também leva o ícone `icon.png` (38x38).

## 2. Enviar para a calculadora

1. Abra o HP Connectivity Kit com a calculadora conectada.
2. Arraste a pasta **Visor.hpappdir** para a calculadora, na seção *Biblioteca de aplicativos*.
3. Na calculadora: tecla **Apps**, depois toque no ícone **Visor**. A primeira página já abre em tela cheia.

## 3. Teclas

| Tecla | Ação |
|---|---|
| Setas | Mover pela página |
| Seta ↓ no fim da página / ↑ no topo | Próxima / anterior |
| ← / → (quando a página cabe na largura) | Página anterior / próxima |
| **+** / **−** | Zoom mais / menos |
| **3** / **9** | Próxima / página anterior |
| Enter | Mostra/oculta a barra de status |
| Esc | Sair |
| Arrastar o dedo na tela | Mover |

## Se algo não funcionar

- **O app abre a tela de funções (F1(X)=…) em vez da página:** o programa do app
  chegou vazio. Na calculadora, aperte Shift + 1 (Programa), escolha "Visor (App)",
  toque em Editar e cole o conteúdo de `saida\Visor_programa.txt` (pelo Connectivity Kit).
- **Se alterar o `Visor.hpppl`:** a firmware 2.4 só aceita o programa do app já
  compilado. Cole o código novo num app no emulador oficial, toque em Verif. e copie o
  `.hpappprgm` gerado em `Documentos\HP Prime\Calculators\Prime\<app>.hpappdir` para
  `Visor_compilado.hpappprgm`. Lembre: o HPPPL aceita no máximo 8 variáveis por `LOCAL`,
  e `e` e `i` são reservados (constante de Euler e unidade imaginária), então não servem como nomes.
- **"Memoria insuficiente p/ este zoom" na barra:** o app voltou um nível de zoom
  sozinho. Use `--zoom-max 2` ou feche outros apps para liberar memória.
- **Erro ao abrir uma página:** confira se os arquivos `p1_1.png` etc. aparecem
  dentro do app no Connectivity Kit.
- **Memória cheia:** use `--zoom-max 2`, `--paginas` ou divida o documento em
  vários apps com `--nome`.

## Licença

[MIT](LICENSE)
