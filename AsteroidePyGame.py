
import pygame
import sys
import math
import random

# ----------------------------------------------------------------------
# CONFIGURACAO GERAL
# ----------------------------------------------------------------------
pygame.init()

LARGURA, ALTURA = 1000, 700
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Impacto de Asteroide - Simulador de Estrago")
relogio = pygame.time.Clock()

# Cores
PRETO = (8, 10, 20)
BRANCO = (240, 240, 240)
CINZA = (90, 95, 110)
CINZA_CLARO = (150, 155, 170)
AZUL_TERRA = (35, 95, 190)
VERDE_TERRA = (45, 130, 70)
AZUL_ESCURO = (15, 40, 90)
LARANJA = (255, 140, 30)
VERMELHO = (220, 40, 30)
AMARELO = (255, 210, 60)
ROXO = (170, 60, 200)
VERDE_OK = (80, 200, 120)

fonte_titulo = pygame.font.SysFont("arial", 30, bold=True)
fonte_label = pygame.font.SysFont("arial", 20, bold=True)
fonte_texto = pygame.font.SysFont("arial", 18)
fonte_pequena = pygame.font.SysFont("arial", 15)
fonte_resultado = pygame.font.SysFont("arial", 19, bold=True)

# ----------------------------------------------------------------------
# FISICA DO IMPACTO (formulas simplificadas para fins didaticos/jogo)
# ----------------------------------------------------------------------
DENSIDADE_ASTEROIDE = 3000  # kg/m3 (asteroide rochoso tipico)
JOULES_POR_TON_TNT = 4.184e9
RAIO_TERRA_KM = 6371

# Eventos reais de referencia (nome, energia em megatons de TNT)
REFERENCIAS = [
    ("uma pequena bomba atomica (Hiroshima, ~15 kt)", 0.015),
    ("o meteoro de Chelyabinsk (2013, Russia)", 0.5),
    ("o evento de Tunguska (1908, Siberia)", 12),
    ("a maior bomba nuclear ja testada (Tsar Bomba)", 50),
    ("um impacto capaz de devastar um pais inteiro", 5000),
    ("o impacto que extinguiu os dinossauros (Chicxulub)", 100_000_000),
]


def calcular_estrago(diametro_m, velocidade_kms):
    """Calcula energia liberada e efeitos de um impacto de asteroide."""
    raio_m = diametro_m / 2
    volume_m3 = (4 / 3) * math.pi * raio_m ** 3
    massa_kg = volume_m3 * DENSIDADE_ASTEROIDE
    velocidade_ms = velocidade_kms * 1000

    energia_j = 0.5 * massa_kg * velocidade_ms ** 2
    energia_ton_tnt = energia_j / JOULES_POR_TON_TNT
    energia_mt_tnt = energia_ton_tnt / 1_000_000

    # Estimativa simplificada de diametro de cratera (formula de escala
    # aproximada, apenas para fins ilustrativos - nao e uma formula
    # cientificamente precisa de crateras de impacto real).
    cratera_km = 0.07 * (max(energia_mt_tnt, 1e-6) ** (1 / 3.4)) * 10

    # Categoria de estrago
    if energia_mt_tnt < 0.001:
        categoria = "Insignificante"
        descricao = "Provavelmente queima na atmosfera antes de chegar ao chao."
        cor = VERDE_OK
    elif energia_mt_tnt < 0.1:
        categoria = "Local"
        descricao = "Destruiria uma cidade pequena ou area ao redor do impacto."
        cor = AMARELO
    elif energia_mt_tnt < 50:
        categoria = "Regional"
        descricao = "Devastaria uma grande regiao, como uma floresta inteira ou area metropolitana."
        cor = LARANJA
    elif energia_mt_tnt < 100_000:
        categoria = "Continental"
        descricao = "Catastrofe continental: milhoes de mortes, mudancas climaticas locais severas."
        cor = VERMELHO
    else:
        categoria = "EXTINCAO EM MASSA"
        descricao = "Impacto capaz de alterar o clima global e causar extincoes em massa."
        cor = ROXO

    # Comparacao com evento real mais proximo
    comparacao = REFERENCIAS[0][0]
    for nome, mt in REFERENCIAS:
        if energia_mt_tnt >= mt:
            comparacao = nome
        else:
            break

    return {
        "massa_kg": massa_kg,
        "energia_j": energia_j,
        "energia_mt_tnt": energia_mt_tnt,
        "cratera_km": cratera_km,
        "categoria": categoria,
        "descricao": descricao,
        "cor": cor,
        "comparacao": comparacao,
    }


# ----------------------------------------------------------------------
# CAIXAS DE TEXTO (INPUT)
# ----------------------------------------------------------------------
class CaixaDeTexto:
    def __init__(self, x, y, largura, altura, texto_inicial=""):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.texto = texto_inicial
        self.ativa = False

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            self.ativa = self.rect.collidepoint(evento.pos)
        elif evento.type == pygame.KEYDOWN and self.ativa:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_TAB):
                self.ativa = False
            elif evento.unicode.isdigit() or (evento.unicode == "." and "." not in self.texto):
                if len(self.texto) < 10:
                    self.texto += evento.unicode

    def desenhar(self, superficie):
        cor_borda = AMARELO if self.ativa else CINZA_CLARO
        pygame.draw.rect(superficie, (25, 28, 40), self.rect, border_radius=6)
        pygame.draw.rect(superficie, cor_borda, self.rect, 2, border_radius=6)
        texto_render = fonte_texto.render(self.texto if self.texto else "0", True, BRANCO)
        superficie.blit(texto_render, (self.rect.x + 10, self.rect.y + 8))


caixa_tamanho = CaixaDeTexto(40, 120, 220, 40, "50")
caixa_velocidade = CaixaDeTexto(40, 205, 220, 40, "20")

botao_calcular = pygame.Rect(40, 270, 220, 50)

# ----------------------------------------------------------------------
# ESTRELAS DE FUNDO
# ----------------------------------------------------------------------
estrelas = [
    (random.randint(300, LARGURA - 20), random.randint(20, ALTURA - 20), random.randint(1, 2))
    for _ in range(120)
]

# ----------------------------------------------------------------------
# ESTADO DA ANIMACAO DE IMPACTO
# ----------------------------------------------------------------------
resultado = None
animando = False
frame_animacao = 0
FRAMES_TOTAIS_EXPLOSAO = 45

CENTRO_TERRA = (680, 400)
RAIO_TERRA_PX = 170


def desenhar_terra(superficie, mostrar_cratera, cratera_raio_px, categoria_cor):
    """Desenha o planeta Terra estilizado."""
    cx, cy = CENTRO_TERRA

    # Brilho/atmosfera
    pygame.draw.circle(superficie, (25, 60, 110), (cx, cy), RAIO_TERRA_PX + 10)

    # Oceano
    pygame.draw.circle(superficie, AZUL_TERRA, (cx, cy), RAIO_TERRA_PX)

    # "Continentes" simples (manchas verdes fixas, apenas decorativas)
    continentes = [
        (cx - 60, cy - 50, 55, 35),
        (cx + 20, cy - 70, 40, 50),
        (cx - 30, cy + 40, 70, 45),
        (cx + 60, cy + 30, 35, 30),
        (cx - 100, cy + 10, 30, 25),
    ]
    mascara = pygame.Surface((RAIO_TERRA_PX * 2, RAIO_TERRA_PX * 2), pygame.SRCALPHA)
    for (mx, my, mw, mh) in continentes:
        pygame.draw.ellipse(superficie, VERDE_TERRA, (mx, my, mw, mh))

    # Sombra lateral pra dar volume
    sombra = pygame.Surface((RAIO_TERRA_PX * 2, RAIO_TERRA_PX * 2), pygame.SRCALPHA)
    pygame.draw.circle(sombra, (0, 0, 0, 90), (RAIO_TERRA_PX + 40, RAIO_TERRA_PX), RAIO_TERRA_PX)
    superficie.blit(sombra, (cx - RAIO_TERRA_PX, cy - RAIO_TERRA_PX))

    # Contorno
    pygame.draw.circle(superficie, (10, 20, 45), (cx, cy), RAIO_TERRA_PX, 3)

    # Cratera pos-impacto
    if mostrar_cratera and cratera_raio_px > 0:
        raio_final = min(cratera_raio_px, RAIO_TERRA_PX - 5)
        pygame.draw.circle(superficie, (60, 25, 15), (cx, cy - RAIO_TERRA_PX + int(raio_final * 0.3)), int(raio_final))
        pygame.draw.circle(superficie, categoria_cor, (cx, cy - RAIO_TERRA_PX + int(raio_final * 0.3)), int(raio_final), 2)


def desenhar_explosao(superficie, frame):
    """Anima uma explosao no ponto de impacto."""
    progresso = frame / FRAMES_TOTAIS_EXPLOSAO
    cx, cy = CENTRO_TERRA
    ponto_impacto = (cx, cy - RAIO_TERRA_PX)

    raio_max = 160
    raio = int(raio_max * progresso)
    alpha = max(0, 255 - int(255 * progresso))

    camada = pygame.Surface((raio_max * 2 + 20, raio_max * 2 + 20), pygame.SRCALPHA)
    centro_camada = (raio_max + 10, raio_max + 10)
    if raio > 0:
        pygame.draw.circle(camada, (255, 210, 60, alpha), centro_camada, raio)
        pygame.draw.circle(camada, (255, 120, 30, alpha), centro_camada, max(raio - 15, 0))
        pygame.draw.circle(camada, (255, 255, 255, alpha), centro_camada, max(raio - 35, 0))
    superficie.blit(camada, (ponto_impacto[0] - centro_camada[0], ponto_impacto[1] - centro_camada[1]))


def formatar_numero(valor):
    """Formata numeros grandes de forma legivel."""
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.2f} milhoes"
    elif valor >= 1_000:
        return f"{valor:,.0f}".replace(",", ".")
    else:
        return f"{valor:.2f}"


# ----------------------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------------------
rodando = True
while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        caixa_tamanho.tratar_evento(evento)
        caixa_velocidade.tratar_evento(evento)

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if botao_calcular.collidepoint(evento.pos):
                try:
                    diametro = float(caixa_tamanho.texto or 0)
                    velocidade = float(caixa_velocidade.texto or 0)
                    if diametro > 0 and velocidade > 0:
                        resultado = calcular_estrago(diametro, velocidade)
                        animando = True
                        frame_animacao = 0
                except ValueError:
                    pass

    # Atualiza animacao
    if animando:
        frame_animacao += 1
        if frame_animacao > FRAMES_TOTAIS_EXPLOSAO:
            animando = False

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    # Estrelas
    for (ex, ey, tam) in estrelas:
        pygame.draw.circle(tela, BRANCO, (ex, ey), tam)

    # Painel esquerdo
    pygame.draw.rect(tela, (18, 20, 32), (0, 0, 300, ALTURA))
    titulo = fonte_titulo.render("IMPACTO DE", True, BRANCO)
    titulo2 = fonte_titulo.render("ASTEROIDE", True, LARANJA)
    tela.blit(titulo, (30, 25))
    tela.blit(titulo2, (30, 58))

    label1 = fonte_label.render("Diametro (metros):", True, CINZA_CLARO)
    tela.blit(label1, (40, 95))
    caixa_tamanho.desenhar(tela)

    label2 = fonte_label.render("Velocidade (km/s):", True, CINZA_CLARO)
    tela.blit(label2, (40, 180))
    caixa_velocidade.desenhar(tela)

    # Botao calcular
    cor_botao = LARANJA if botao_calcular.collidepoint(pygame.mouse.get_pos()) else (200, 100, 20)
    pygame.draw.rect(tela, cor_botao, botao_calcular, border_radius=8)
    texto_botao = fonte_label.render("CALCULAR ESTRAGO", True, PRETO)
    tela.blit(texto_botao, texto_botao.get_rect(center=botao_calcular.center))

    # Resultados
    if resultado:
        y = 350
        pygame.draw.line(tela, CINZA, (30, y - 15), (270, y - 15), 1)

        cat_render = fonte_resultado.render(f"Categoria: {resultado['categoria']}", True, resultado["cor"])
        tela.blit(cat_render, (30, y))
        y += 35

        linhas_desc = []
        palavras = resultado["descricao"].split(" ")
        linha_atual = ""
        for palavra in palavras:
            teste = (linha_atual + " " + palavra).strip()
            if fonte_pequena.size(teste)[0] > 250:
                linhas_desc.append(linha_atual)
                linha_atual = palavra
            else:
                linha_atual = teste
        linhas_desc.append(linha_atual)
        for linha in linhas_desc:
            tela.blit(fonte_pequena.render(linha, True, BRANCO), (30, y))
            y += 20

        y += 10
        info = [
            f"Massa: {formatar_numero(resultado['massa_kg'])} kg",
            f"Energia: {resultado['energia_j']:.2e} J",
            f"Equivalente: {formatar_numero(resultado['energia_mt_tnt'])} Mt TNT",
            f"Cratera estimada: ~{resultado['cratera_km']:.2f} km",
        ]
        for linha in info:
            tela.blit(fonte_pequena.render(linha, True, CINZA_CLARO), (30, y))
            y += 22

        y += 10
        tela.blit(fonte_pequena.render("Comparavel a:", True, AMARELO), (30, y))
        y += 20
        palavras = resultado["comparacao"].split(" ")
        linha_atual = ""
        for palavra in palavras:
            teste = (linha_atual + " " + palavra).strip()
            if fonte_pequena.size(teste)[0] > 250:
                tela.blit(fonte_pequena.render(linha_atual, True, BRANCO), (30, y))
                y += 20
                linha_atual = palavra
            else:
                linha_atual = teste
        tela.blit(fonte_pequena.render(linha_atual, True, BRANCO), (30, y))

    # Planeta Terra
    mostrar_cratera = resultado is not None and not animando
    cratera_px = 0
    cor_cat = VERMELHO
    if resultado:
        escala = RAIO_TERRA_PX / RAIO_TERRA_KM
        cratera_px = max(resultado["cratera_km"] * escala, 4)
        cor_cat = resultado["cor"]

    desenhar_terra(tela, mostrar_cratera, cratera_px, cor_cat)

    if animando:
        desenhar_explosao(tela, frame_animacao)

    # Asteroide (representacao antes do impacto, so decorativo)
    if not resultado:
        ax, ay = CENTRO_TERRA[0] - 40, CENTRO_TERRA[1] - RAIO_TERRA_PX - 90
        pygame.draw.circle(tela, CINZA, (ax, ay), 14)
        pygame.draw.circle(tela, CINZA_CLARO, (ax - 4, ay - 4), 4)
        seta_texto = fonte_pequena.render("Asteroide se aproximando...", True, CINZA_CLARO)
        tela.blit(seta_texto, (ax - 90, ay + 25))

    # Rodape
    rodape = fonte_pequena.render(
        "Formulas simplificadas para fins ilustrativos - nao representam precisao cientifica exata.",
        True, (110, 115, 130)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 30))

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
sys.exit()
