from pathlib import Path
import re

import qrcode
from PIL import Image, ImageDraw, ImageFont

LARGURA = 1004
ALTURA = 638
DPI = 300
AZUL_ESCURO = "#003366"
PASTA_SAIDA = Path(__file__).resolve().parent / "carteirinhas_fisicas"

alunos_demonstracao = [
    {"id": "2026001", "nome": "Ana Beatriz Oliveira", "turma": "5º Ano A"},
    {"id": "2026002", "nome": "Lucas Ferreira Santos", "turma": "6º Ano B"},
    {"id": "2026003", "nome": "Mariana Costa Almeida", "turma": "7º Ano A"},
]


def carregar_fonte(tamanho):
    fontes = [
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for caminho in fontes:
        if caminho.is_file():
            return ImageFont.truetype(str(caminho), tamanho)
    return ImageFont.load_default(size=tamanho)


def ajustar_texto(texto, draw, largura_maxima, tamanho_inicial, tamanho_minimo=26):
    for tamanho in range(tamanho_inicial, tamanho_minimo - 1, -2):
        fonte = carregar_fonte(tamanho)
        if draw.textbbox((0, 0), texto, font=fonte)[2] <= largura_maxima:
            return fonte, texto

    fonte = carregar_fonte(tamanho_minimo)
    texto_curto = texto
    while texto_curto and draw.textbbox(
        (0, 0), texto_curto + "...", font=fonte
    )[2] > largura_maxima:
        texto_curto = texto_curto[:-1]
    return fonte, texto_curto.rstrip() + "..."


def gerar_qr(id_aluno):
    codigo = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    codigo.add_data(id_aluno)
    codigo.make(fit=True)
    imagem = codigo.make_image(fill_color="black", back_color="white").convert("RGB")
    return imagem.resize((320, 320), Image.Resampling.NEAREST)


def gerar_carteirinha(aluno, pasta_saida=PASTA_SAIDA):
    id_aluno = str(aluno["id"]).strip()
    nome = str(aluno["nome"]).strip()
    turma = str(aluno["turma"]).strip()
    if not id_aluno or not nome or not turma:
        raise ValueError("Cada aluno precisa ter ID, Nome e Turma preenchidos.")

    imagem = Image.new("RGB", (LARGURA, ALTURA), "#FFFFFF")
    draw = ImageDraw.Draw(imagem)

    draw.rectangle((0, 0, LARGURA, 142), fill=AZUL_ESCURO)
    fonte_titulo = carregar_fonte(38)
    titulo = "SISTEMA ESCOLAR DE ENSINO"
    titulo_caixa = draw.textbbox((0, 0), titulo, font=fonte_titulo)
    titulo_largura = titulo_caixa[2] - titulo_caixa[0]
    draw.text(
        ((LARGURA - titulo_largura) // 2, 48),
        titulo,
        fill="#FFFFFF",
        font=fonte_titulo,
    )
    draw.rectangle((0, 142, LARGURA, 153), fill="#D3A62B")
    draw.rounded_rectangle(
        (18, 18, LARGURA - 18, ALTURA - 18),
        radius=24,
        outline="#D8E0E8",
        width=3,
    )

    x_texto = 58
    largura_texto = 510
    fonte_rotulo = carregar_fonte(23)
    draw.text((x_texto, 205), "NOME", fill="#526273", font=fonte_rotulo)
    fonte_nome, nome_exibido = ajustar_texto(nome, draw, largura_texto, 43)
    draw.text((x_texto, 239), nome_exibido, fill=AZUL_ESCURO, font=fonte_nome)

    draw.line((x_texto, 330, x_texto + largura_texto, 330), fill="#E1E7ED", width=2)
    draw.text((x_texto, 355), "TURMA", fill="#526273", font=fonte_rotulo)
    fonte_turma, turma_exibida = ajustar_texto(turma, draw, largura_texto, 38)
    draw.text((x_texto, 389), turma_exibida, fill="#172B3D", font=fonte_turma)

    draw.line((x_texto, 463, x_texto + largura_texto, 463), fill="#E1E7ED", width=2)
    draw.text((x_texto, 486), "ID / MATRÍCULA", fill="#526273", font=fonte_rotulo)
    fonte_id, id_exibido = ajustar_texto(id_aluno, draw, largura_texto, 34)
    draw.text((x_texto, 522), id_exibido, fill="#172B3D", font=fonte_id)

    qr_x, qr_y = 634, 231
    draw.rounded_rectangle(
        (qr_x - 11, qr_y - 11, qr_x + 331, qr_y + 331),
        radius=14,
        fill="#FFFFFF",
        outline="#D8E0E8",
        width=2,
    )
    imagem.paste(gerar_qr(id_aluno), (qr_x, qr_y))

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    nome_arquivo = re.sub(r"[^A-Za-z0-9_-]", "_", id_aluno)
    caminho = pasta_saida / f"carteirinha_{nome_arquivo}.png"
    imagem.save(caminho, format="PNG", dpi=(DPI, DPI), optimize=True)
    return caminho


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    for aluno in alunos_demonstracao:
        caminho = gerar_carteirinha(aluno)
        print(f"Carteirinha gerada: {caminho}")


if __name__ == "__main__":
    main()
