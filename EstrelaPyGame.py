"""
ASCENSAO DE UMA ESTRELA - Simulador
=======================================
Controle o GAS disponivel, a TEMPERATURA e a GRAVIDADE/PRESSAO de uma
nuvem cosmica. Dependendo do equilibrio entre os tres, ela pode virar
uma protoestrela, uma estrela da sequencia principal (ana vermelha,
tipo Sol, azul-branca, supergigante) ou, se tudo estiver no limite,
explodir em uma supernova e deixar como resto uma estrela de neutrons
ou um buraco negro.

Como rodar:
    pip install pygame
    python ascensao_estrela.py
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
pygame.display.set_caption("Ascensao de uma Estrela")
relogio = pygame.time.Clock()

PRETO = (5, 5, 10)
BRANCO = (245, 245, 250)
CINZA = (90, 95, 110)
CINZA_CLARO = (160, 165, 180)
AMARELO = (255, 210, 90)
LARANJA = (255, 140, 40)
VERMELHO = (230, 60, 50)
AZUL = (110, 170, 255)
ROXO = (170, 90, 230)
VERDE_OK = (90, 210, 140)
PAINEL_BG = (16, 18, 28)

fonte_titulo = pygame.font.SysFont("arial", 27, bold=True)
fonte_label = pygame.font.SysFont("arial", 18, bold=True)
fonte_texto = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 14)
fonte_status = pygame.font.SysFont("arial", 22, bold=True)

CENTRO = (660, 400)

# ----------------------------------------------------------------------
# ESTADO DO SISTEMA
# ----------------------------------------------------------------------
gas = 10
temperatura = 10
gravidade = 10

# valores suavizados (para animacao fluida das transicoes)
gas_suave = float(gas)
temperatura_suave = float(temperatura)
gravidade_suave = float(gravidade)

LIMIAR_IGNICAO_GAS = 15
LIMIAR_IGNICAO_TEMP = 35
LIMIAR_IGNICAO_GRAV = 35

LIMIAR_SUPERNOVA = 85  # os 3 parametros precisam passar disso

TOTAL_FRAMES_EXPLOSAO = 55
frame_explosao = 0
supernova_estado_anterior = False

# Particulas da nuvem de gas / protoestrela
NUM_PARTICULAS = 260
particulas = []
for _ in range(NUM_PARTICULAS):
    particulas.append({
        "angulo": random.uniform(0, math.tau),
        "fator_raio": random.uniform(0.25, 1.0),
        "vel_rotacao": random.uniform(0.5, 1.6),
        "tamanho": random.uniform(1, 2.6),
    })

# Estrelas de fundo
estrelas_fundo = [
    (random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 2), random.uniform(0.3, 1))
    for _ in range(150)
]

tempo = 0

# ----------------------------------------------------------------------
# BOTOES
# ----------------------------------------------------------------------
def criar_botao(x, y):
    return pygame.Rect(x, y, 44, 38)

botao_gas_menos = criar_botao(40, 122)
botao_gas_mais = criar_botao(220, 122)

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
def calcular_estado(gas, temperatura, gravidade):
    ignicao = (gas >= LIMIAR_IGNICAO_GAS and temperatura >= LIMIAR_IGNICAO_TEMP
               and gravidade >= LIMIAR_IGNICAO_GRAV)
    supernova = (gas >= LIMIAR_SUPERNOVA and temperatura >= LIMIAR_SUPERNOVA
                 and gravidade >= LIMIAR_SUPERNOVA)

    if supernova:
        tipo = "supernova"
    elif not ignicao:
        tipo = "nebulosa" if gas < LIMIAR_IGNICAO_GAS else "protoestrela"
    else:
        if gas < 35:
            tipo = "ana_vermelha"
        elif gas < 60:
            tipo = "tipo_sol"
        elif gas < 80:
            tipo = "azul_branca"
        else:
            tipo = "supergigante"

    return tipo, ignicao, supernova


INFO_TIPOS = {
    "nebulosa": ("Nuvem de Gas Dispersa", CINZA_CLARO,
                 "Como a Nebulosa de Orion antes da formacao de estrelas."),
    "protoestrela": ("Protoestrela em Colapso", AMARELO,
                      "Semelhante as protoestrelas encontradas na Nebulosa de Carina."),
    "ana_vermelha": ("Ana Vermelha (Sequencia Principal)", LARANJA,
                       "Parecida com Proxima Centauri, a estrela mais proxima do Sol."),
    "tipo_sol": ("Estrela tipo Sol (Sequencia Principal)", AMARELO,
                  "Muito parecida com o nosso Sol (tipo espectral G)."),
    "azul_branca": ("Estrela Azul-Branca (Sequencia Principal)", AZUL,
                      "Comparavel a Sirius A, uma estrela azul-branca brilhante."),
    "supergigante": ("Supergigante Azul (Instavel)", ROXO,
                       "Rivaliza com Rigel, uma supergigante azul massiva e instavel."),
}


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


# ----------------------------------------------------------------------
# DESENHO
# ----------------------------------------------------------------------
def desenhar_nuvem_particulas(gas_v, temp_v, grav_v, tempo):
    raio_alvo = 200 * (1 - (grav_v / 100) * 0.82)
    num_visiveis = int(NUM_PARTICULAS * max(gas_v, 3) / 100)
    cor_base = cor_por_temperatura(temp_v)

    for p in particulas[:num_visiveis]:
        p["angulo"] += 0.0025 * p["vel_rotacao"] * (1 + grav_v / 60)
        r = raio_alvo * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"])
        y = CENTRO[1] + r * math.sin(p["angulo"])
        escurecimento = 0.6 + 0.4 * (1 - p["fator_raio"])
        cor = tuple(int(c * escurecimento) for c in cor_base)
        pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_estrela_solida(tipo, gas_v, temp_v):
    cor = cor_por_temperatura(temp_v)
    raio_core = 26 + gas_v * 0.55

    # Glow / corona (varios circulos translucidos)
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for i, escala in enumerate((2.4, 1.9, 1.4)):
        alpha = 45 - i * 12
        pygame.draw.circle(camada, (*cor, max(alpha, 8)), CENTRO, int(raio_core * escala))
    tela.blit(camada, (0, 0))

    pygame.draw.circle(tela, cor, CENTRO, int(raio_core))
    borda = tuple(min(255, c + 30) for c in cor)
    pygame.draw.circle(tela, borda, CENTRO, int(raio_core), 2)


def desenhar_explosao_supernova(frame):
    progresso = frame / TOTAL_FRAMES_EXPLOSAO
    raio_max = 260
    raio = int(raio_max * progresso)
    alpha = max(0, 255 - int(255 * progresso))

    camada = pygame.Surface((raio_max * 2 + 20, raio_max * 2 + 20), pygame.SRCALPHA)
    centro_camada = (raio_max + 10, raio_max + 10)
    if raio > 0:
        pygame.draw.circle(camada, (255, 255, 255, alpha), centro_camada, raio)
        pygame.draw.circle(camada, (255, 210, 120, alpha), centro_camada, max(raio - 25, 0))
        pygame.draw.circle(camada, (255, 120, 60, alpha), centro_camada, max(raio - 55, 0))
    tela.blit(camada, (CENTRO[0] - centro_camada[0], CENTRO[1] - centro_camada[1]))


def desenhar_remanescente(buraco_negro, tempo):
    if buraco_negro:
        raio = 34
        pygame.draw.circle(tela, (255, 200, 140), CENTRO, raio + 5, 2)
        pygame.draw.circle(tela, PRETO, CENTRO, raio)
        pygame.draw.circle(tela, (20, 10, 5), CENTRO, raio, 2)
    else:
        pulso = 1 + 0.15 * math.sin(tempo * 0.01)
        raio = int(16 * pulso)
        camada = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(camada, (150, 200, 255, 70), (100, 100), raio + 25)
        tela.blit(camada, (CENTRO[0] - 100, CENTRO[1] - 100))
        pygame.draw.circle(tela, (220, 235, 255), CENTRO, raio)
        pygame.draw.circle(tela, (150, 200, 255), CENTRO, raio, 2)


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
            if botao_gas_mais.collidepoint(evento.pos):
                gas = min(100, gas + 5)
            elif botao_gas_menos.collidepoint(evento.pos):
                gas = max(0, gas - 5)
            elif botao_temp_mais.collidepoint(evento.pos):
                temperatura = min(100, temperatura + 5)
            elif botao_temp_menos.collidepoint(evento.pos):
                temperatura = max(0, temperatura - 5)
            elif botao_grav_mais.collidepoint(evento.pos):
                gravidade = min(100, gravidade + 5)
            elif botao_grav_menos.collidepoint(evento.pos):
                gravidade = max(0, gravidade - 5)

    # suavizacao das transicoes
    gas_suave += (gas - gas_suave) * 0.08
    temperatura_suave += (temperatura - temperatura_suave) * 0.08
    gravidade_suave += (gravidade - gravidade_suave) * 0.08

    tipo, ignicao, supernova = calcular_estado(gas, temperatura, gravidade)

    # controle da animacao de supernova (deteccao de borda)
    if supernova and not supernova_estado_anterior:
        frame_explosao = 1
    elif supernova:
        if frame_explosao < TOTAL_FRAMES_EXPLOSAO + 1:
            frame_explosao += 1
    else:
        frame_explosao = 0
    supernova_estado_anterior = supernova

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    for (ex, ey, tam, fase) in estrelas_fundo:
        brilho = int(120 + 100 * math.sin(tempo * 0.001 * fase + ex))
        brilho = max(60, min(255, brilho))
        pygame.draw.circle(tela, (brilho, brilho, brilho), (ex, ey), tam)

    # Painel esquerdo
    pygame.draw.rect(tela, PAINEL_BG, (0, 0, 300, ALTURA))
    tela.blit(fonte_titulo.render("ASCENSAO DE", True, BRANCO), (30, 20))
    tela.blit(fonte_titulo.render("UMA ESTRELA", True, LARANJA), (30, 50))

    # GAS
    tela.blit(fonte_label.render("GAS", True, CINZA_CLARO), (40, 95))
    desenhar_botao(botao_gas_menos, "-", botao_gas_menos.collidepoint(mouse_pos), LARANJA)
    desenhar_botao(botao_gas_mais, "+", botao_gas_mais.collidepoint(mouse_pos), LARANJA)
    desenhar_barra(95, 130, 115, 24, gas, LARANJA)
    tela.blit(fonte_texto.render(f"{gas}/100", True, BRANCO), (100, 134))

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

    y_status = 425
    if supernova:
        if frame_explosao <= TOTAL_FRAMES_EXPLOSAO:
            status_txt, cor_status = "SUPERNOVA!", VERMELHO
        else:
            buraco_negro = gas >= 95
            status_txt = "Buraco Negro" if buraco_negro else "Estrela de Neutrons"
            cor_status = ROXO if buraco_negro else AZUL
        comparacao = ("O nucleo colapsou em um buraco negro, como Cygnus X-1."
                      if (frame_explosao > TOTAL_FRAMES_EXPLOSAO and gas >= 95)
                      else "Restou uma estrela de neutrons supercompacta, como as que geram pulsares."
                      if frame_explosao > TOTAL_FRAMES_EXPLOSAO
                      else "O nucleo da estrela colapsou violentamente sob seu proprio peso.")
    else:
        status_txt, cor_status, comparacao = INFO_TIPOS[tipo]

    for linha in texto_em_linhas(status_txt, fonte_status, 250):
        tela.blit(fonte_status.render(linha, True, cor_status), (30, y_status))
        y_status += 28

    y_status += 8
    tela.blit(fonte_pequena.render("Comparavel a:", True, AMARELO), (30, y_status))
    y_status += 20
    for linha in texto_em_linhas(comparacao, fonte_pequena, 250):
        tela.blit(fonte_pequena.render(linha, True, BRANCO), (30, y_status))
        y_status += 18

    if not ignicao and not supernova:
        y_status += 20
        for linha in texto_em_linhas(
            f"Dica: gas >= {LIMIAR_IGNICAO_GAS}, temperatura e gravidade >= {LIMIAR_IGNICAO_TEMP} para a fusao comecar.",
            fonte_pequena, 250
        ):
            tela.blit(fonte_pequena.render(linha, True, CINZA), (30, y_status))
            y_status += 16
    elif not supernova:
        y_status += 20
        for linha in texto_em_linhas(
            f"Dica: gas, temperatura e gravidade >= {LIMIAR_SUPERNOVA} para uma supernova.",
            fonte_pequena, 250
        ):
            tela.blit(fonte_pequena.render(linha, True, CINZA), (30, y_status))
            y_status += 16

    # -------------------- VISUALIZACAO CENTRAL --------------------
    if supernova:
        if frame_explosao <= TOTAL_FRAMES_EXPLOSAO:
            desenhar_estrela_solida("supergigante", 90, 95)
            desenhar_explosao_supernova(frame_explosao)
        else:
            desenhar_remanescente(gas >= 95, tempo)
    elif ignicao:
        desenhar_estrela_solida(tipo, gas_suave, temperatura_suave)
    else:
        desenhar_nuvem_particulas(gas_suave, temperatura_suave, gravidade_suave, tempo)

    rodape = fonte_pequena.render(
        "Simulacao ilustrativa - representa de forma simplificada a formacao e o fim de uma estrela.",
        True, (100, 105, 120)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 26))

    pygame.display.flip()

pygame.quit()
sys.exit()
