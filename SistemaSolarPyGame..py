"""
FORMACAO DE UM SISTEMA SOLAR - Simulador
=============================================
Controle a MASSA do disco protoplanetario, a TEMPERATURA da estrela
central e a GRAVIDADE do sistema. Uma estrela se acende no centro e,
conforme o disco de gas e poeira ao redor se condensa, ate 5 orbitas
podem formar planetas - de rochosos escaldantes perto da estrela ate
gigantes gasosos e de gelo nas orbitas mais distantes e frias.

Como rodar:
    pip install pygame
    python formacao_sistema_solar.py
"""

import pygame
import sys
import math
import random

# ----------------------------------------------------------------------
# CONFIGURACAO GERAL
# ----------------------------------------------------------------------
pygame.init()

LARGURA, ALTURA = 1000, 760
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Formacao de um Sistema Solar")
relogio = pygame.time.Clock()

PRETO = (5, 5, 10)
BRANCO = (245, 245, 250)
CINZA = (90, 95, 110)
CINZA_CLARO = (160, 165, 180)
AMARELO = (255, 215, 120)
LARANJA = (255, 150, 60)
VERMELHO = (225, 90, 65)
AZUL = (120, 175, 255)
VERDE = (100, 205, 130)
MARROM = (150, 110, 70)
PAINEL_BG = (16, 18, 28)

fonte_titulo = pygame.font.SysFont("arial", 26, bold=True)
fonte_label = pygame.font.SysFont("arial", 18, bold=True)
fonte_texto = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 14)
fonte_status = pygame.font.SysFont("arial", 19, bold=True)

CENTRO = (660, 400)

# ----------------------------------------------------------------------
# ESTADO DO SISTEMA
# ----------------------------------------------------------------------
massa = 10
temperatura = 50
gravidade = 10

massa_suave = float(massa)
temperatura_suave = float(temperatura)
gravidade_suave = float(gravidade)

LIMIAR_ESTRELA_MASSA = 15
LIMIAR_ESTRELA_GRAVIDADE = 25
LIMIAR_DISCO_DIFUSO = 20      # abaixo disso: disco bem espalhado
LIMIAR_SISTEMA_FORMADO = 45   # acima disso: planetas discretos aparecem

NUM_ANEIS = 5
RAIOS_ANEL = [85, 140, 195, 250, 305]
REQUISITO_MASSA_ANEL = [10, 25, 40, 55, 70]
QUEDA_TEMP_POR_ANEL = 22

angulos_orbita = [random.uniform(0, math.tau) for _ in range(NUM_ANEIS)]
velocidade_orbita = [0.028 / ((i + 1) ** 1.15) for i in range(NUM_ANEIS)]

tempo = 0
fase_nuvem = 0.0

# ----------------------------------------------------------------------
# PARTICULAS DO DISCO
# ----------------------------------------------------------------------
NUM_PARTICULAS = 260
particulas_disco = [{
    "angulo": random.uniform(0, math.tau),
    "fator_raio": random.uniform(0.15, 1.0),
    "vel": random.uniform(0.4, 1.3),
    "tamanho": random.uniform(1, 2.4),
} for _ in range(NUM_PARTICULAS)]

estrelas_fundo = [
    (random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 2), random.uniform(0.3, 1))
    for _ in range(150)
]

# ----------------------------------------------------------------------
# BOTOES
# ----------------------------------------------------------------------
def criar_botao(x, y):
    return pygame.Rect(x, y, 44, 38)

botao_massa_menos = criar_botao(40, 122)
botao_massa_mais = criar_botao(220, 122)

botao_temp_menos = criar_botao(40, 225)
botao_temp_mais = criar_botao(220, 225)

botao_grav_menos = criar_botao(40, 328)
botao_grav_mais = criar_botao(220, 328)


def desenhar_botao(rect, texto, hover, cor_base):
    cor = cor_base if hover else tuple(max(0, c - 70) for c in cor_base)
    pygame.draw.rect(tela, cor, rect, border_radius=8)
    pygame.draw.rect(tela, CINZA_CLARO, rect, 2, border_radius=8)
    render = fonte_label.render(texto, True, PRETO if hover else BRANCO)
    tela.blit(render, render.get_rect(center=rect.center))


def desenhar_barra(x, y, largura, altura, valor, cor):
    pygame.draw.rect(tela, (35, 38, 50), (x, y, largura, altura), border_radius=6)
    largura_preenchida = int(largura * (valor / 100))
    if largura_preenchida > 0:
        pygame.draw.rect(tela, cor, (x, y, largura_preenchida, altura), border_radius=6)
    pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura, altura), 2, border_radius=6)


def texto_em_linhas(texto, fonte, largura_max):
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        if fonte.size(teste)[0] > largura_max:
            linhas.append(linha_atual)
            linha_atual = palavra
        else:
            linha_atual = teste
    linhas.append(linha_atual)
    return linhas


# ----------------------------------------------------------------------
# FISICA / CLASSIFICACAO (simplificadas para fins de jogo)
# ----------------------------------------------------------------------
def cor_por_temperatura(temp):
    paradas = [
        (0, (150, 40, 30)),
        (25, (220, 90, 40)),
        (50, (255, 160, 60)),
        (70, (255, 220, 140)),
        (85, (255, 250, 235)),
        (100, (170, 205, 255)),
    ]
    temp = max(0, min(100, temp))
    for i in range(len(paradas) - 1):
        t0, c0 = paradas[i]
        t1, c1 = paradas[i + 1]
        if t0 <= temp <= t1:
            frac = (temp - t0) / (t1 - t0) if t1 != t0 else 0
            return tuple(int(c0[j] + (c1[j] - c0[j]) * frac) for j in range(3))
    return paradas[-1][1]


def classificar_anel(indice, massa_v, temperatura_v):
    if massa_v < REQUISITO_MASSA_ANEL[indice]:
        return "vazio"

    temp_local = max(0, temperatura_v - indice * QUEDA_TEMP_POR_ANEL)

    if temp_local < 40:
        if massa_v >= 80:
            return "gigante_gasoso"
        elif massa_v >= 60:
            return "gigante_gelo"
        else:
            return "gelado"
    else:
        if temp_local >= 70:
            return "rochoso_quente"
        else:
            return "rochoso"


INFO_ANEL = {
    "vazio": ("Vazio (cinturao de detritos)", CINZA_CLARO),
    "gelado": ("Planeta Gelado", (190, 220, 255)),
    "gigante_gelo": ("Gigante de Gelo", (140, 205, 230)),
    "gigante_gasoso": ("Gigante Gasoso", (220, 175, 120)),
    "rochoso_quente": ("Rochoso Escaldante", VERMELHO),
    "rochoso": ("Rochoso tipo Terra", VERDE),
}


def comentario_geral(tipos_aneis):
    contagem_gigantes = sum(1 for t in tipos_aneis if t in ("gigante_gasoso", "gigante_gelo"))
    contagem_rochosos = sum(1 for t in tipos_aneis if t in ("rochoso", "rochoso_quente"))
    contagem_vazios = sum(1 for t in tipos_aneis if t == "vazio")

    if contagem_vazios == NUM_ANEIS:
        return "Nenhuma orbita conseguiu reter material ainda."
    if contagem_gigantes >= 1 and contagem_rochosos >= 2 and tipos_aneis[0] != "vazio":
        return "Parecido com o nosso proprio Sistema Solar: rochosos por perto, gigantes mais longe!"
    if contagem_gigantes == 0 and contagem_rochosos >= 1:
        return "Um sistema so com planetas rochosos, sem nenhum gigante gasoso."
    if contagem_gigantes >= 3:
        return "Um sistema dominado por gigantes, incomum e rico em gas."
    return "Um sistema planetario ainda em formacao, com composicao irregular."


# ----------------------------------------------------------------------
# DESENHO
# ----------------------------------------------------------------------
def desenhar_disco_particulas(massa_v, gravidade_v, fase):
    raio_max = RAIOS_ANEL[-1] + 40
    raio_alvo = raio_max * (1 - (gravidade_v / 100) * 0.45)
    num_visiveis = int(NUM_PARTICULAS * max(massa_v, 6) / 100)

    for p in particulas_disco[:num_visiveis]:
        p["angulo"] += 0.0018 * p["vel"]
        r = raio_alvo * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"])
        y = CENTRO[1] + r * math.sin(p["angulo"]) * 0.55
        pygame.draw.circle(tela, (160, 140, 110), (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_orbitas():
    for r in RAIOS_ANEL:
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pygame.draw.ellipse(camada, (90, 95, 120, 60),
                             (CENTRO[0] - r, CENTRO[1] - r * 0.55, r * 2, r * 1.1), 1)
        tela.blit(camada, (0, 0))


def desenhar_estrela(temperatura_v, massa_v):
    cor = cor_por_temperatura(temperatura_v)
    raio = 18 + massa_v * 0.12

    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for i, escala in enumerate((2.6, 2.0, 1.4)):
        alpha = 40 - i * 10
        pygame.draw.circle(camada, (*cor, max(alpha, 8)), CENTRO, int(raio * escala))
    tela.blit(camada, (0, 0))

    pygame.draw.circle(tela, cor, CENTRO, int(raio))
    pygame.draw.circle(tela, tuple(min(255, c + 30) for c in cor), CENTRO, int(raio), 2)


def desenhar_esfera_com_faixas(centro, raio, cores, fase):
    diam = max(2, int(raio * 2))
    bandas = pygame.Surface((diam, diam), pygame.SRCALPHA)
    n = len(cores) * 3
    altura_faixa = diam / n
    deslocamento = (fase * 40) % altura_faixa
    for i in range(-1, n + 1):
        cor = cores[i % len(cores)]
        y0 = i * altura_faixa + deslocamento
        pygame.draw.rect(bandas, (*cor, 255), (0, y0, diam, altura_faixa + 1))

    mascara = pygame.Surface((diam, diam), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (diam // 2, diam // 2), diam // 2)
    bandas.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    tela.blit(bandas, (centro[0] - diam // 2, centro[1] - diam // 2))
    pygame.draw.circle(tela, tuple(max(0, c - 50) for c in cores[0]), centro, int(raio), 2)


def desenhar_planeta(indice, tipo, massa_v, fase):
    r_orbita = RAIOS_ANEL[indice]
    angulos_orbita[indice] += velocidade_orbita[indice] * (1 + gravidade_suave / 150)
    ang = angulos_orbita[indice]

    x = CENTRO[0] + r_orbita * math.cos(ang)
    y = CENTRO[1] + r_orbita * math.sin(ang) * 0.55
    pos = (int(x), int(y))

    fator_massa = 0.7 + 0.3 * (massa_v / 100)

    if tipo == "vazio":
        # cinturao de detritos: alguns pontinhos fracos ao longo da orbita
        for k in range(6):
            ang2 = ang + k * (math.tau / 6)
            xx = CENTRO[0] + r_orbita * math.cos(ang2)
            yy = CENTRO[1] + r_orbita * math.sin(ang2) * 0.55
            pygame.draw.circle(tela, (100, 95, 90), (int(xx), int(yy)), 2)
        return

    if tipo == "rochoso_quente":
        raio_p = 9 * fator_massa
        pygame.draw.circle(tela, (150, 45, 30), pos, int(raio_p))
        pygame.draw.circle(tela, (255, 150, 60), pos, max(1, int(raio_p * 0.4)))

    elif tipo == "rochoso":
        raio_p = 10 * fator_massa
        pygame.draw.circle(tela, (35, 110, 190), pos, int(raio_p))
        pygame.draw.circle(tela, (60, 150, 80), (pos[0] - int(raio_p * 0.3), pos[1] - int(raio_p * 0.2)),
                            max(1, int(raio_p * 0.45)))

    elif tipo == "gelado":
        raio_p = 9 * fator_massa
        pygame.draw.circle(tela, (210, 235, 255), pos, int(raio_p))
        pygame.draw.circle(tela, (160, 195, 230), pos, int(raio_p), 1)

    elif tipo == "gigante_gelo":
        raio_p = 16 * fator_massa
        desenhar_esfera_com_faixas(pos, raio_p, [(150, 210, 230), (110, 175, 210), (170, 225, 240)], fase)

    elif tipo == "gigante_gasoso":
        raio_p = 22 * fator_massa
        desenhar_esfera_com_faixas(pos, raio_p, [(215, 175, 130), (185, 130, 85), (235, 200, 155), (165, 110, 70)], fase)

    pygame.draw.circle(tela, CINZA, pos, 1)


# ----------------------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------------------
rodando = True
while rodando:
    dt_ms = relogio.tick(60)
    tempo += dt_ms
    mouse_pos = pygame.mouse.get_pos()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if botao_massa_mais.collidepoint(evento.pos):
                massa = min(100, massa + 5)
            elif botao_massa_menos.collidepoint(evento.pos):
                massa = max(0, massa - 5)
            elif botao_temp_mais.collidepoint(evento.pos):
                temperatura = min(100, temperatura + 5)
            elif botao_temp_menos.collidepoint(evento.pos):
                temperatura = max(0, temperatura - 5)
            elif botao_grav_mais.collidepoint(evento.pos):
                gravidade = min(100, gravidade + 5)
            elif botao_grav_menos.collidepoint(evento.pos):
                gravidade = max(0, gravidade - 5)

    massa_suave += (massa - massa_suave) * 0.08
    temperatura_suave += (temperatura - temperatura_suave) * 0.08
    gravidade_suave += (gravidade - gravidade_suave) * 0.08
    fase_nuvem += 0.01

    estrela_formada = massa >= LIMIAR_ESTRELA_MASSA and gravidade >= LIMIAR_ESTRELA_GRAVIDADE
    sistema_formado = gravidade >= LIMIAR_SISTEMA_FORMADO

    if sistema_formado:
        tipos_aneis = [classificar_anel(i, massa, temperatura) for i in range(NUM_ANEIS)]
    else:
        tipos_aneis = None

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    for (ex, ey, tam, fase_estrela) in estrelas_fundo:
        brilho = int(120 + 100 * math.sin(tempo * 0.001 * fase_estrela + ex))
        brilho = max(60, min(255, brilho))
        pygame.draw.circle(tela, (brilho, brilho, brilho), (ex, ey), tam)

    # Painel esquerdo
    pygame.draw.rect(tela, PAINEL_BG, (0, 0, 300, ALTURA))
    tela.blit(fonte_titulo.render("FORMACAO DE UM", True, BRANCO), (30, 20))
    tela.blit(fonte_titulo.render("SISTEMA SOLAR", True, LARANJA), (30, 50))

    # MASSA
    tela.blit(fonte_label.render("MASSA DO DISCO", True, CINZA_CLARO), (40, 95))
    desenhar_botao(botao_massa_menos, "-", botao_massa_menos.collidepoint(mouse_pos), MARROM)
    desenhar_botao(botao_massa_mais, "+", botao_massa_mais.collidepoint(mouse_pos), MARROM)
    desenhar_barra(95, 130, 115, 24, massa, MARROM)
    tela.blit(fonte_texto.render(f"{massa}/100", True, BRANCO), (100, 134))

    # TEMPERATURA
    tela.blit(fonte_label.render("TEMPERATURA", True, CINZA_CLARO), (40, 198))
    desenhar_botao(botao_temp_menos, "-", botao_temp_menos.collidepoint(mouse_pos), VERMELHO)
    desenhar_botao(botao_temp_mais, "+", botao_temp_mais.collidepoint(mouse_pos), VERMELHO)
    desenhar_barra(95, 233, 115, 24, temperatura, VERMELHO)
    tela.blit(fonte_texto.render(f"{temperatura}/100", True, BRANCO), (100, 237))

    # GRAVIDADE
    tela.blit(fonte_label.render("GRAVIDADE", True, CINZA_CLARO), (40, 301))
    desenhar_botao(botao_grav_menos, "-", botao_grav_menos.collidepoint(mouse_pos), AZUL)
    desenhar_botao(botao_grav_mais, "+", botao_grav_mais.collidepoint(mouse_pos), AZUL)
    desenhar_barra(95, 336, 115, 24, gravidade, AZUL)
    tela.blit(fonte_texto.render(f"{gravidade}/100", True, BRANCO), (100, 340))

    # Status
    pygame.draw.line(tela, CINZA, (30, 385), (270, 385), 1)
    tela.blit(fonte_label.render("STATUS:", True, CINZA_CLARO), (30, 398))

    y_status = 422
    if not estrela_formada:
        estagio_txt, cor_estagio = "Disco Protoplanetario (sem estrela)", CINZA_CLARO
    elif not sistema_formado:
        estagio_txt, cor_estagio = "Estrela Acesa - Disco Condensando", AMARELO
    else:
        estagio_txt, cor_estagio = "Sistema Solar Formado", VERDE

    for linha in texto_em_linhas(estagio_txt, fonte_status, 250):
        tela.blit(fonte_status.render(linha, True, cor_estagio), (30, y_status))
        y_status += 25

    y_status += 6
    if tipos_aneis is not None:
        for i, tipo in enumerate(tipos_aneis):
            nome, cor = INFO_ANEL[tipo]
            linha = f"Orbita {i + 1}: {nome}"
            for l in texto_em_linhas(linha, fonte_pequena, 250):
                tela.blit(fonte_pequena.render(l, True, cor), (30, y_status))
                y_status += 17

        y_status += 8
        tela.blit(fonte_pequena.render("Resumo:", True, AMARELO), (30, y_status))
        y_status += 18
        for linha in texto_em_linhas(comentario_geral(tipos_aneis), fonte_pequena, 250):
            tela.blit(fonte_pequena.render(linha, True, BRANCO), (30, y_status))
            y_status += 17
    else:
        if not estrela_formada:
            dica = f"Dica: massa >= {LIMIAR_ESTRELA_MASSA} e gravidade >= {LIMIAR_ESTRELA_GRAVIDADE} para acender a estrela."
        else:
            dica = f"Dica: gravidade >= {LIMIAR_SISTEMA_FORMADO} para os planetas se formarem."
        for linha in texto_em_linhas(dica, fonte_pequena, 250):
            tela.blit(fonte_pequena.render(linha, True, CINZA), (30, y_status))
            y_status += 17

    # -------------------- VISUALIZACAO CENTRAL --------------------
    desenhar_orbitas()

    if not sistema_formado:
        desenhar_disco_particulas(massa_suave, gravidade_suave, fase_nuvem)

    if estrela_formada:
        desenhar_estrela(temperatura_suave, massa_suave)

    if sistema_formado:
        for i, tipo in enumerate(tipos_aneis):
            desenhar_planeta(i, tipo, massa_suave, fase_nuvem)

    rodape = fonte_pequena.render(
        "Simulacao ilustrativa - representa de forma simplificada a formacao de um sistema planetario.",
        True, (100, 105, 120)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 26))

    pygame.display.flip()

pygame.quit()
sys.exit()
