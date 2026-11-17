"""
Conversor de imagens e PDFs para o app "Visor" da HP Prime.

Uso:
    python visor_hp.py arquivo1.pdf foto.jpg ... [-o pasta_saida] [--nome Visor]
                      [--zoom-max 3] [--paginas 1-10] [--cinza]

Gera <pasta_saida>/<Nome>.hpappdir, pronto para arrastar no
HP Connectivity Kit, contendo uma imagem PNG por pagina e por nivel de zoom
(ja na resolucao da tela de 320x240), mais o programa do visor.
"""
import argparse
import os
import shutil
import sys

from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:  # PDFs ficam indisponiveis, imagens continuam funcionando
    fitz = None

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
TELA_L, TELA_A = 320, 240
FATORES = [1.0, 1.5, 2.0, 3.0, 4.0]   # multiplos da largura da tela
LADO_MAX = 4096                        # maior lado de um nivel de zoom
BLOCO_L, BLOCO_A = 480, 360            # tamanho dos blocos (igual ao Visor.hpppl)
AQUI = os.path.dirname(os.path.abspath(__file__))
EXT_IMG = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}


def larguras_alvo(w, h, zoom_max, nativa=None):
    """Larguras (em pixels) de cada nivel de zoom para uma pagina w x h."""
    ajuste_pagina = min(TELA_L / w, TELA_A / h) * w
    niveis = []
    if ajuste_pagina < TELA_L * 0.9:
        niveis.append(ajuste_pagina)          # pagina inteira na tela
    for f in FATORES:
        if f > zoom_max + 1e-9:
            break
        niveis.append(TELA_L * f)             # ajustar largura, 1.5x, 2x...
    limite = LADO_MAX / max(1.0, h / w)        # nao passar de LADO_MAX de altura
    if nativa:                                 # imagens: nao ampliar demais
        limite = min(limite, max(nativa * 1.25, TELA_L))
    saida = [round(x) for x in niveis if x <= limite + 0.5]
    return saida or [round(min(niveis[0], limite))]


def fatiar_alta(img):
    """Divide imagens muito compridas (ex.: prints longos) em varias paginas."""
    w, h = img.size
    if h <= 4 * w:
        return [img]
    passo = 3 * w
    sobra = w // 10                            # pequena sobreposicao
    partes, y = [], 0
    while y < h:
        partes.append(img.crop((0, y, w, min(h, y + passo + sobra))))
        y += passo
    return partes


def para_rgb(img):
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        fundo = Image.new("RGB", img.size, (255, 255, 255))
        fundo.paste(img, mask=img.split()[-1])
        return fundo
    return img.convert("RGB")


def parse_intervalo(txt, total):
    if not txt:
        return list(range(total))
    sel = []
    for parte in txt.split(","):
        if "-" in parte:
            a, b = parte.split("-")
            sel.extend(range(int(a) - 1, min(int(b), total)))
        else:
            sel.append(int(parte) - 1)
    return [i for i in sel if 0 <= i < total]


def paginas_de(caminho, args):
    """Gera tuplas (renderizar(largura)->Image, w, h, largura_nativa)."""
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".pdf":
        if fitz is None:
            sys.exit("Para PDFs instale o PyMuPDF:  python -m pip install pymupdf")
        doc = fitz.open(caminho)
        for i in parse_intervalo(args.paginas, doc.page_count):
            pag = doc[i]
            w, h = pag.rect.width, pag.rect.height

            def render(largura, pag=pag, w=w):
                z = largura / w
                pix = pag.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
                return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            yield render, w, h, None
    elif ext in EXT_IMG:
        img = Image.open(caminho)
        quadros = []
        try:                                    # GIF/TIFF com varios quadros
            for n in range(getattr(img, "n_frames", 1)):
                img.seek(n)
                quadros.append(para_rgb(img.copy()))
        except EOFError:
            pass
        for q in quadros:
            for parte in fatiar_alta(q):
                def render(largura, parte=parte):
                    a = max(1, round(parte.height * largura / parte.width))
                    return parte.resize((largura, a), LANCZOS)

                yield render, parte.width, parte.height, parte.width
    else:
        print(f"  ignorado (formato nao suportado): {caminho}")


def gravar_programa(destino_prgm, destino_txt):
    # A firmware 2.4 so aceita o programa do app ja compilado (formato binario).
    # Visor_compilado.hpappprgm foi gerado colando Visor.hpppl no emulador
    # oficial; se mudar o Visor.hpppl, gere esse arquivo de novo do mesmo jeito.
    shutil.copyfile(os.path.join(AQUI, "Visor_compilado.hpappprgm"), destino_prgm)
    with open(os.path.join(AQUI, "Visor.hpppl"), encoding="utf-8") as f:
        fonte = f.read()
    with open(destino_txt, "w", encoding="utf-8", newline="") as f:
        f.write(fonte.replace("\r\n", "\n").replace("\n", "\r\n"))


def main():
    ap = argparse.ArgumentParser(description="Converte imagens/PDF para o Visor da HP Prime")
    ap.add_argument("arquivos", nargs="+", help="imagens e/ou PDFs, na ordem desejada")
    ap.add_argument("-o", "--saida", default="saida", help="pasta de saida (padrao: saida)")
    ap.add_argument("--nome", default="Visor", help="nome do app na calculadora")
    ap.add_argument("--zoom-max", type=float, default=3.0,
                    help="zoom maximo, em vezes a largura da tela (1 a 4, padrao 3)")
    ap.add_argument("--paginas", help="paginas dos PDFs, ex.: 1-5,8")
    ap.add_argument("--cinza", action="store_true", help="converte para tons de cinza")
    args = ap.parse_args()

    appdir = os.path.join(args.saida, args.nome + ".hpappdir")
    if os.path.isdir(appdir):
        shutil.rmtree(appdir)
    os.makedirs(appdir)

    n_pag, total = 0, 0
    for caminho in args.arquivos:
        print(f"{caminho}")
        for render, w, h, nativa in paginas_de(caminho, args):
            n_pag += 1
            larguras = larguras_alvo(w, h, args.zoom_max, nativa)
            for nivel, largura in enumerate(larguras, start=1):
                img = render(largura)
                if args.cinza:
                    img = img.convert("L").convert("RGB")
                # blocos de BLOCO_L x BLOCO_A: a calculadora so carrega os visiveis
                for c, x in enumerate(range(0, img.width, BLOCO_L), start=1):
                    for r, y in enumerate(range(0, img.height, BLOCO_A), start=1):
                        bloco = img.crop((x, y, min(img.width, x + BLOCO_L),
                                          min(img.height, y + BLOCO_A)))
                        nome = os.path.join(appdir, f"p{n_pag}_{nivel}_{c}_{r}.png")
                        bloco.save(nome, optimize=True)
                        total += os.path.getsize(nome)
            print(f"  pagina {n_pag}: {len(larguras)} niveis de zoom "
                  f"({', '.join(str(x) for x in larguras)} px de largura)")

    if n_pag == 0:
        sys.exit("Nenhuma pagina gerada.")

    shutil.copyfile(os.path.join(AQUI, "base_app.hpapp"),
                    os.path.join(appdir, args.nome + ".hpapp"))
    shutil.copyfile(os.path.join(AQUI, "icon.png"), os.path.join(appdir, "icon.png"))
    gravar_programa(os.path.join(appdir, args.nome + ".hpappprgm"),
                    os.path.join(args.saida, args.nome + "_programa.txt"))

    print(f"\nPronto: {n_pag} paginas, {total / 1024 / 1024:.1f} MB em imagens")
    print(f"App gerado em: {os.path.abspath(appdir)}")
    print("Arraste essa pasta para a calculadora no HP Connectivity Kit.")


if __name__ == "__main__":
    main()
