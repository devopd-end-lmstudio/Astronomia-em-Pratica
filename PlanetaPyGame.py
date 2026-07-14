"""
ASCENSAO DE UM PLANETA - Simulador
=======================================
Controle a quantidade de ASTEROIDES que vao se juntar, a TEMPERATURA e a
GRAVIDADE/PRESSAO do sistema. Dependendo do equilibrio entre os tres,
os asteroides podem continuar dispersos, colidir caoticamente sem se
unir, formar um protoplaneta, ou virar um planeta completo - rochoso,
gelado, oceanico, uma super-Terra ou ate um gigante gasoso.

Como rodar:
    pip install pygame
    python ascensao_planeta.py
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
pygame.display.set_caption("Ascensao de um Planeta")
relogio = pygame.time.Clock()

PRETO = (5, 5, 10)
BRANCO = (245, 245, 250)
CINZA = (90, 95, 110)
CINZA_CLARO = (160, 165, 180)
AMARELO = (255, 210, 90)
LARANJA = (255, 140, 40)
VERMELHO = (230, 60, 50)
AZUL = (110, 170, 255)
VERDE = (100, 200, 120)
MARROM = (150, 110, 70)
PAINEL_BG = (16, 18, 28)

fonte_titulo = pygame.font.SysFont("arial", 27, bold=True)
fonte_label = pygame.font.SysFont("arial", 18, bold=True)
fonte_texto = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 14)
fonte_status = pygame.font.SysFont("arial", 21, bold=True)

CENTRO = (660, 400)

# ----------------------------------------------------------------------
# ESTADO DO SISTEMA
# ----------------------------------------------------------------------
asteroides = 10
temperatura = 50
gravidade = 10

asteroides_suave = float(asteroides)
temperatura_suave = float(temperatura)
gravidade_suave = float(gravidade)

LIMIAR_ASTEROIDES_MIN = 15       # minimo para comecar a se aglomerar
LIMIAR_GRAVIDADE_CAOS = 20       # abaixo disso, so colisoes caoticas
LIMIAR_GRAVIDADE_FORMADO = 40    # acima disso, planeta esferico completo
LIMIAR_TEMP_EVAPORACAO = 90      # atmosfera evapora se muito quente e pouca massa

tempo = 0

# Particulas do cinturao de asteroides / debris
NUM_PARTICULAS = 240
particulas = []
for _ in range(NUM_PARTICULAS):
    particulas.append({
        "angulo": random.uniform(0, math.tau),
        "fator_raio": random.uniform(0.4, 1.0),
        "vel_rotacao": random.uniform(0.4, 1.4),
        "tamanho": random.uniform(1.5, 3.2),
    })

# Perfil irregular (bumps fixos) para corpos rochosos ainda em formacao
PERFIL_IRREGULAR = [random.uniform(-0.12, 0.12) for _ in range(32)]

# Particulas de atmosfera evaporando (nucleo exposto)
particulas_evaporando = []
for _ in range(50):
    particulas_evaporando.append({
        "angulo": random.uniform(0, math.tau),
        "dist": random.uniform(0, 1),
        "vel": random.uniform(0.6, 1.6),
    })

# Faiscas de colisao (estagio caotico)
faiscas = []

# Estrelas de fundo
estrelas_fundo = [
    (random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 2), random.uniform(0.3, 1))
    for _ in range(150)
]

# ----------------------------------------------------------------------
# BOTOES
# ----------------------------------------------------------------------
def criar_botao(x, y):
    return pygame.Rect(x, y, 44, 38)

botao_ast_menos = criar_botao(40, 122)
botao_ast_mais = criar_botao(220, 122)

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
# CLASSIFICACAO (simplificada para fins de jogo)
# ----------------------------------------------------------------------
def calcular_estado(asteroides, temperatura, gravidade):
    if asteroides < LIMIAR_ASTEROIDES_MIN:
        return "disperso"
    if gravidade < LIMIAR_GRAVIDADE_CAOS:
        return "caotico"
    if gravidade < LIMIAR_GRAVIDADE_FORMADO:
        return "protoplaneta"

    # formado - planeta esferico completo
    if temperatura >= LIMIAR_TEMP_EVAPORACAO and asteroides < 40:
        return "nucleo_exposto"

    if asteroides < 40:
        if temperatura < 40:
            return "gelado"
        elif temperatura < 70:
            return "terrestre"
        else:
            return "rochoso_quente"
    elif asteroides < 70:
        if temperatura < 50:
            return "oceanico"
        else:
            return "super_terra"
    else:
        if temperatura < 60:
            return "gigante_gasoso"
        else:
            return "jupiter_quente"


INFO_TIPOS = {
    "disperso": ("Cinturao de Asteroides Disperso", CINZA_CLARO,
                  "Como o Cinturao de Asteroides entre Marte e Jupiter."),
    "caotico": ("Colisoes Caoticas (gravidade insuficiente)", AMARELO,
                 "Fragmentos se chocam sem conseguir se unir, como em um disco protoplanetario jovem e turbulento."),
    "protoplaneta": ("Protoplaneta em Formacao", LARANJA,
                       "Semelhante a Vesta ou Ceres, corpos que quase viraram planetas."),
    "nucleo_exposto": ("Nucleo Rochoso Exposto (atmosfera evaporada)", VERMELHO,
                          "Um mundo lavico exposto, com a atmosfera arrancada pelo calor extremo."),
    "gelado": ("Planeta Gelado", (180, 220, 255),
                "Parecido com um planeta gelado distante, como uma versao maior de Plutao."),
    "terrestre": ("Planeta Rochoso tipo Terra", VERDE,
                   "Muito parecido com a Terra, em equilibrio de temperatura."),
    "rochoso_quente": ("Planeta Rochoso Escaldante", VERMELHO,
                         "Comparavel a Venus ou Mercurio, extremamente quente."),
    "oceanico": ("Planeta Oceanico", AZUL,
                  "Um mundo coberto de agua, como os hipoteticos planetas-oceano."),
    "super_terra": ("Super-Terra", MARROM,
                      "Maior e mais massiva que a Terra, mas ainda rochosa, como Kepler-452b."),
    "gigante_gasoso": ("Gigante Gasoso", (210, 160, 110),
                         "Parecido com Jupiter ou Saturno, um gigante de gas frio."),
    "jupiter_quente": ("Jupiter Quente ('Hot Jupiter')", LARANJA,
                          "Como os gigantes gasosos que orbitam bem perto de suas estrelas."),
}


# ----------------------------------------------------------------------
# DESENHO
# ----------------------------------------------------------------------
def raio_do_nucleo(asteroides_v):
    return 20 + asteroides_v * 0.9


def desenhar_nuvem_particulas(asteroides_v, gravidade_v, estagio, tempo):
    raio_alvo = 230 * (1 - (gravidade_v / 100) * 0.6)
    num_visiveis = int(NUM_PARTICULAS * max(asteroides_v, 6) / 100)
    turbulencia = 1.0 if estagio != "caotico" else 2.6

    for p in particulas[:num_visiveis]:
        p["angulo"] += 0.002 * p["vel_rotacao"] * turbulencia
        r = raio_alvo * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"])
        y = CENTRO[1] + r * math.sin(p["angulo"])
        cor = (150, 130, 110) if estagio == "disperso" else (170, 130, 90)
        pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))

    # faiscas de colisao no estagio caotico
    if estagio == "caotico":
        if random.random() < 0.5:
            ang = random.uniform(0, math.tau)
            r = random.uniform(0, raio_alvo)
            fx = CENTRO[0] + r * math.cos(ang)
            fy = CENTRO[1] + r * math.sin(ang)
            faiscas.append({"pos": (fx, fy), "vida": 12})
        for f in faiscas[:]:
            f["vida"] -= 1
            if f["vida"] <= 0:
                faiscas.remove(f)
            else:
                pygame.draw.circle(tela, (255, 230, 150), (int(f["pos"][0]), int(f["pos"][1])), 3)


def desenhar_protoplaneta(asteroides_v, gravidade_v, tempo):
    raio = raio_do_nucleo(asteroides_v)
    progresso_suavizacao = min(1.0, (gravidade_v - LIMIAR_GRAVIDADE_CAOS) /
                                (LIMIAR_GRAVIDADE_FORMADO - LIMIAR_GRAVIDADE_CAOS))
    intensidade_bumps = 1 - progresso_suavizacao

    pontos = []
    n = len(PERFIL_IRREGULAR)
    for i, bump in enumerate(PERFIL_IRREGULAR):
        ang = (i / n) * math.tau
        r = raio * (1 + bump * intensidade_bumps)
        x = CENTRO[0] + r * math.cos(ang)
        y = CENTRO[1] + r * math.sin(ang)
        pontos.append((x, y))

    pygame.draw.polygon(tela, (140, 110, 85), pontos)
    pygame.draw.polygon(tela, (90, 70, 55), pontos, 2)

    # debris restante orbitando, diminuindo conforme se aproxima de formado
    num_debris = int(40 * intensidade_bumps)
    for p in particulas[:num_debris]:
        p["angulo"] += 0.0035 * p["vel_rotacao"]
        r = raio + 60 + 25 * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"])
        y = CENTRO[1] + r * math.sin(p["angulo"])
        pygame.draw.circle(tela, (170, 140, 100), (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_esfera_com_faixas(centro, raio, cores, tempo):
    diam = max(2, int(raio * 2))
    bandas = pygame.Surface((diam, diam), pygame.SRCALPHA)
    n = len(cores) * 3
    altura_faixa = diam / n
    deslocamento = (tempo * 0.01) % altura_faixa
    for i in range(-1, n + 1):
        cor = cores[i % len(cores)]
        y0 = i * altura_faixa + deslocamento
        pygame.draw.rect(bandas, (*cor, 255), (0, y0, diam, altura_faixa + 1))

    mascara = pygame.Surface((diam, diam), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (diam // 2, diam // 2), diam // 2)
    bandas.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    tela.blit(bandas, (centro[0] - diam // 2, centro[1] - diam // 2))
    pygame.draw.circle(tela, tuple(max(0, c - 50) for c in cores[0]), centro, int(raio), 2)


def desenhar_planeta_formado(tipo, asteroides_v, tempo):
    cx, cy = CENTRO
    raio = raio_do_nucleo(asteroides_v)

    if tipo == "gelado":
        pygame.draw.circle(tela, (215, 235, 255), CENTRO, int(raio))
        pygame.draw.ellipse(tela, (235, 248, 255), (cx - raio * 0.5, cy - raio * 0.6, raio * 0.7, raio * 0.5))
        pygame.draw.circle(tela, (160, 195, 230), CENTRO, int(raio), 2)

    elif tipo == "terrestre":
        pygame.draw.circle(tela, (35, 110, 190), CENTRO, int(raio))
        for (dx, dy, w, h) in [
            (-raio * 0.35, -raio * 0.35, raio * 0.55, raio * 0.4),
            (raio * 0.05, -raio * 0.5, raio * 0.4, raio * 0.45),
            (-raio * 0.2, raio * 0.2, raio * 0.6, raio * 0.4),
        ]:
            pygame.draw.ellipse(tela, (55, 145, 80), (cx + dx, cy + dy, w, h))
        pygame.draw.circle(tela, (20, 55, 100), CENTRO, int(raio), 2)

    elif tipo == "oceanico":
        pygame.draw.circle(tela, (18, 85, 165), CENTRO, int(raio))
        pygame.draw.ellipse(tela, (60, 150, 220), (cx - raio * 0.4, cy - raio * 0.3, raio * 0.8, raio * 0.35))
        pygame.draw.circle(tela, (10, 45, 95), CENTRO, int(raio), 2)

    elif tipo == "super_terra":
        pygame.draw.circle(tela, (95, 115, 70), CENTRO, int(raio))
        for (dx, dy, w, h) in [
            (-raio * 0.3, -raio * 0.3, raio * 0.5, raio * 0.35),
            (raio * 0.1, raio * 0.15, raio * 0.45, raio * 0.35),
        ]:
            pygame.draw.ellipse(tela, (120, 90, 60), (cx + dx, cy + dy, w, h))
        pygame.draw.circle(tela, (45, 55, 35), CENTRO, int(raio), 2)

    elif tipo in ("rochoso_quente", "nucleo_exposto"):
        cor_base = (150, 40, 25) if tipo == "rochoso_quente" else (60, 22, 16)
        pygame.draw.circle(tela, cor_base, CENTRO, int(raio))
        for i in range(6):
            ang = tempo * 0.0012 + i * (math.tau / 6)
            x1 = cx + raio * 0.1 * math.cos(ang)
            y1 = cy + raio * 0.1 * math.sin(ang)
            x2 = cx + raio * 0.92 * math.cos(ang + 0.35)
            y2 = cy + raio * 0.92 * math.sin(ang + 0.35)
            pygame.draw.line(tela, (255, 150, 40), (x1, y1), (x2, y2), 2)
        pygame.draw.circle(tela, (25, 10, 5), CENTRO, int(raio), 2)

        if tipo == "nucleo_exposto":
            for p in particulas_evaporando:
                p["dist"] += p["vel"] * 0.01
                if p["dist"] > 1.6:
                    p["dist"] = 0
                    p["angulo"] = random.uniform(0, math.tau)
                d = raio * (1 + p["dist"])
                x = cx + d * math.cos(p["angulo"])
                y = cy + d * math.sin(p["angulo"])
                alpha_frac = max(0, 1 - p["dist"] / 1.6)
                tam = max(1, int(3 * alpha_frac))
                cor_p = (255, int(160 * alpha_frac) + 40, int(60 * alpha_frac))
                pygame.draw.circle(tela, cor_p, (int(x), int(y)), tam)

    elif tipo == "gigante_gasoso":
        cores = [(215, 175, 130), (185, 130, 85), (235, 200, 155), (165, 110, 70)]
        desenhar_esfera_com_faixas(CENTRO, raio * 1.6, cores, tempo)

    elif tipo == "jupiter_quente":
        cores = [(255, 150, 70), (225, 95, 45), (255, 190, 100), (205, 75, 35)]
        desenhar_esfera_com_faixas(CENTRO, raio * 1.6, cores, tempo)
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pygame.draw.circle(camada, (255, 140, 60, 40), CENTRO, int(raio * 1.6 * 1.25))
        tela.blit(camada, (0, 0))


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
            if botao_ast_mais.collidepoint(evento.pos):
                asteroides = min(100, asteroides + 5)
            elif botao_ast_menos.collidepoint(evento.pos):
                asteroides = max(0, asteroides - 5)
            elif botao_temp_mais.collidepoint(evento.pos):
                temperatura = min(100, temperatura + 5)
            elif botao_temp_menos.collidepoint(evento.pos):
                temperatura = max(0, temperatura - 5)
            elif botao_grav_mais.collidepoint(evento.pos):
                gravidade = min(100, gravidade + 5)
            elif botao_grav_menos.collidepoint(evento.pos):
                gravidade = max(0, gravidade - 5)

    asteroides_suave += (asteroides - asteroides_suave) * 0.08
    temperatura_suave += (temperatura - temperatura_suave) * 0.08
    gravidade_suave += (gravidade - gravidade_suave) * 0.08

    estagio = calcular_estado(asteroides, temperatura, gravidade)
    formado = estagio not in ("disperso", "caotico", "protoplaneta")

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    for (ex, ey, tam, fase) in estrelas_fundo:
        brilho = int(120 + 100 * math.sin(tempo * 0.001 * fase + ex))
        brilho = max(60, min(255, brilho))
        pygame.draw.circle(tela, (brilho, brilho, brilho), (ex, ey), tam)

    # Painel esquerdo
    pygame.draw.rect(tela, PAINEL_BG, (0, 0, 300, ALTURA))
    tela.blit(fonte_titulo.render("ASCENSAO DE", True, BRANCO), (30, 20))
    tela.blit(fonte_titulo.render("UM PLANETA", True, VERDE), (30, 50))

    # ASTEROIDES
    tela.blit(fonte_label.render("ASTEROIDES", True, CINZA_CLARO), (40, 95))
    desenhar_botao(botao_ast_menos, "-", botao_ast_menos.collidepoint(mouse_pos), MARROM)
    desenhar_botao(botao_ast_mais, "+", botao_ast_mais.collidepoint(mouse_pos), MARROM)
    desenhar_barra(95, 130, 115, 24, asteroides, MARROM)
    tela.blit(fonte_texto.render(f"{asteroides}/100", True, BRANCO), (100, 134))

    # TEMPERATURA
    tela.blit(fonte_label.render("TEMPERATURA", True, CINZA_CLARO), (40, 198))
    desenhar_botao(botao_temp_menos, "-", botao_temp_menos.collidepoint(mouse_pos), VERMELHO)
    desenhar_botao(botao_temp_mais, "+", botao_temp_mais.collidepoint(mouse_pos), VERMELHO)
    desenhar_barra(95, 233, 115, 24, temperatura, VERMELHO)
    tela.blit(fonte_texto.render(f"{temperatura}/100", True, BRANCO), (100, 237))

    # GRAVIDADE / PRESSAO
    tela.blit(fonte_label.render("GRAVIDADE / PRESSAO", True, CINZA_CLARO), (40, 301))
    desenhar_botao(botao_grav_menos, "-", botao_grav_menos.collidepoint(mouse_pos), AZUL)
    desenhar_botao(botao_grav_mais, "+", botao_grav_mais.collidepoint(mouse_pos), AZUL)
    desenhar_barra(95, 336, 115, 24, gravidade, AZUL)
    tela.blit(fonte_texto.render(f"{gravidade}/100", True, BRANCO), (100, 340))

    # Status
    pygame.draw.line(tela, CINZA, (30, 385), (270, 385), 1)
    tela.blit(fonte_label.render("STATUS:", True, CINZA_CLARO), (30, 398))

    nome_status, cor_status, comparacao = INFO_TIPOS[estagio]
    y_status = 425
    for linha in texto_em_linhas(nome_status, fonte_status, 250):
        tela.blit(fonte_status.render(linha, True, cor_status), (30, y_status))
        y_status += 27

    y_status += 8
    tela.blit(fonte_pequena.render("Comparavel a:", True, AMARELO), (30, y_status))
    y_status += 20
    for linha in texto_em_linhas(comparacao, fonte_pequena, 250):
        tela.blit(fonte_pequena.render(linha, True, BRANCO), (30, y_status))
        y_status += 18

    if not formado:
        y_status += 20
        if asteroides < LIMIAR_ASTEROIDES_MIN:
            dica = f"Dica: junte pelo menos {LIMIAR_ASTEROIDES_MIN} de asteroides."
        elif gravidade < LIMIAR_GRAVIDADE_CAOS:
            dica = f"Dica: gravidade >= {LIMIAR_GRAVIDADE_CAOS} para parar de colidir ao acaso."
        else:
            dica = f"Dica: gravidade >= {LIMIAR_GRAVIDADE_FORMADO} para virar um planeta esferico."
        for linha in texto_em_linhas(dica, fonte_pequena, 250):
            tela.blit(fonte_pequena.render(linha, True, CINZA), (30, y_status))
            y_status += 16

    # -------------------- VISUALIZACAO CENTRAL --------------------
    if estagio in ("disperso", "caotico"):
        desenhar_nuvem_particulas(asteroides_suave, gravidade_suave, estagio, tempo)
    elif estagio == "protoplaneta":
        desenhar_protoplaneta(asteroides_suave, gravidade_suave, tempo)
    else:
        desenhar_planeta_formado(estagio, asteroides_suave, tempo)

    rodape = fonte_pequena.render(
        "Simulacao ilustrativa - representa de forma simplificada a acrecao e formacao de planetas.",
        True, (100, 105, 120)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 26))

    pygame.display.flip()

pygame.quit()
sys.exit()
