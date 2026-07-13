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
pygame.display.set_caption("Ascensao de um Quasar")
relogio = pygame.time.Clock()

PRETO = (5, 5, 10)
BRANCO = (245, 245, 250)
CINZA = (90, 95, 110)
CINZA_CLARO = (160, 165, 180)
AZUL_JATO = (100, 170, 255)
ROXO_JATO = (170, 90, 255)
LARANJA = (255, 140, 40)
AMARELO = (255, 210, 90)
VERMELHO = (230, 60, 50)
VERDE_OK = (90, 210, 140)
PAINEL_BG = (16, 18, 28)

fonte_titulo = pygame.font.SysFont("arial", 28, bold=True)
fonte_label = pygame.font.SysFont("arial", 19, bold=True)
fonte_texto = pygame.font.SysFont("arial", 17)
fonte_pequena = pygame.font.SysFont("arial", 14)
fonte_status = pygame.font.SysFont("arial", 24, bold=True)

CENTRO = (660, 380)

# ----------------------------------------------------------------------
# ESTADO DO SISTEMA
# ----------------------------------------------------------------------
massa = 20          # 0 a 100 (escala arbitraria de "massas solares" x1e6)
gas = 15            # 0 a 100 (percentual de gas disponivel ao redor)

LIMIAR_MASSA_QUASAR = 50
LIMIAR_GAS_QUASAR = 50

angulo_disco = 0.0
tempo = 0

# Particulas do disco de acrecao
particulas_disco = []
for _ in range(220):
    particulas_disco.append({
        "angulo": random.uniform(0, math.tau),
        "raio_rel": random.uniform(0.35, 1.0),  # posicao relativa dentro do disco
        "velocidade": random.uniform(0.6, 1.6),
        "tamanho": random.uniform(1, 2.6),
    })

# Particulas dos jatos (raios gama)
particulas_jato_cima = []
particulas_jato_baixo = []
for _ in range(60):
    particulas_jato_cima.append({"dist": random.uniform(0, 1), "vel": random.uniform(3, 7), "desvio": random.uniform(-6, 6)})
    particulas_jato_baixo.append({"dist": random.uniform(0, 1), "vel": random.uniform(3, 7), "desvio": random.uniform(-6, 6)})

# Estrelas de fundo
estrelas = [
    (random.randint(0, LARGURA), random.randint(0, ALTURA), random.randint(1, 2), random.uniform(0.3, 1))
    for _ in range(160)
]

# ----------------------------------------------------------------------
# BOTOES
# ----------------------------------------------------------------------
def criar_botao(x, y, texto):
    rect = pygame.Rect(x, y, 44, 40)
    return rect, texto

botao_massa_menos, _ = criar_botao(40, 130, "-")
botao_massa_mais, _ = criar_botao(220, 130, "+")
botao_gas_menos, _ = criar_botao(40, 245, "-")
botao_gas_mais, _ = criar_botao(220, 245, "+")


def desenhar_botao(rect, texto, hover):
    cor = LARANJA if hover else (70, 40, 20)
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


# ----------------------------------------------------------------------
# CALCULOS
# ----------------------------------------------------------------------
def calcular_estado(massa, gas):
    """Retorna o nivel de atividade do sistema e status textual."""
    ativo_quasar = massa >= LIMIAR_MASSA_QUASAR and gas >= LIMIAR_GAS_QUASAR
    luminosidade = (massa * gas) / 100  # 0 a 100, unidade arbitraria

    if massa < 15:
        status = "Buraco negro dormente"
        cor = CINZA_CLARO
    elif gas < 15:
        status = "Buraco negro isolado (sem material ao redor)"
        cor = CINZA_CLARO
    elif not ativo_quasar and (massa >= LIMIAR_MASSA_QUASAR or gas >= LIMIAR_GAS_QUASAR):
        status = "Disco de acrecao se formando..."
        cor = AMARELO
    elif ativo_quasar and luminosidade < 80:
        status = "QUASAR ATIVO!"
        cor = LARANJA
    elif ativo_quasar:
        status = "QUASAR HIPERLUMINOSO!"
        cor = VERMELHO
    else:
        status = "Nucleo galatico levemente ativo"
        cor = VERDE_OK

    return ativo_quasar, luminosidade, status, cor


def comparacao_real(luminosidade, ativo):
    if not ativo:
        return "Um buraco negro comum, sem atividade significativa."
    if luminosidade < 30:
        return "Um nucleo galatico ativo (AGN) de baixa luminosidade."
    if luminosidade < 60:
        return "Comparavel a Centaurus A, uma radiogalaxia proxima."
    if luminosidade < 85:
        return "Comparavel a 3C 273, um dos quasares mais brilhantes conhecidos."
    return "Rivaliza com os quasares mais luminosos do universo observavel, como J0529-4351."


# ----------------------------------------------------------------------
# DESENHO DO SISTEMA
# ----------------------------------------------------------------------
def desenhar_buraco_negro(raio_bh):
    # Brilho externo (photon ring)
    for i in range(6, 0, -1):
        alpha_cor = tuple(min(255, c) for c in (40, 20, 10))
    pygame.draw.circle(tela, (255, 200, 140), CENTRO, raio_bh + 6, 2)
    pygame.draw.circle(tela, PRETO, CENTRO, raio_bh)
    pygame.draw.circle(tela, (20, 10, 5), CENTRO, raio_bh, 2)


def desenhar_disco(raio_bh, raio_disco, intensidade, dt_angulo):
    global angulo_disco
    angulo_disco += dt_angulo

    # Base elipsada do disco (visto em perspectiva)
    achatamento = 0.32

    for p in particulas_disco:
        p["angulo"] += 0.003 * p["velocidade"] * (1 + intensidade / 50)
        raio_p = raio_bh + (raio_disco - raio_bh) * p["raio_rel"]
        x = CENTRO[0] + raio_p * math.cos(p["angulo"])
        y = CENTRO[1] + raio_p * math.sin(p["angulo"]) * achatamento

        # cor varia de laranja (frio) a branco-azulado (quente/gas intenso)
        t = min(1.0, intensidade / 100)
        cor = (
            int(200 + 55 * t),
            int(90 + 130 * t),
            int(30 + 200 * t),
        )

        # Nao desenha particulas "atras" do buraco negro (aprox. simples)
        atras = math.sin(p["angulo"]) > 0 and abs(x - CENTRO[0]) < raio_bh
        if not atras:
            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_jatos(intensidade, raio_bh):
    """Desenha os jatos de raios gama saindo dos polos do buraco negro."""
    comprimento_jato = 60 + intensidade * 2.6

    for direcao, lista in ((-1, particulas_jato_cima), (1, particulas_jato_baixo)):
        # Cone de luz (glow) do jato
        largura_base = 10 + intensidade * 0.12
        ponta = (CENTRO[0], CENTRO[1] + direcao * (raio_bh + comprimento_jato))
        base_esq = (CENTRO[0] - largura_base, CENTRO[1] + direcao * raio_bh)
        base_dir = (CENTRO[0] + largura_base, CENTRO[1] + direcao * raio_bh)

        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pygame.draw.polygon(camada, (*ROXO_JATO, 70), [base_esq, base_dir, ponta])
        tela.blit(camada, (0, 0))
        pygame.draw.polygon(tela, (*AZUL_JATO, ), [base_esq, base_dir, ponta], 2)

        # Particulas correndo pelo jato
        for part in lista:
            part["dist"] += part["vel"] / comprimento_jato * 0.02
            if part["dist"] > 1:
                part["dist"] = 0
                part["desvio"] = random.uniform(-6, 6)
                part["vel"] = random.uniform(3, 7)

            dist_px = raio_bh + part["dist"] * comprimento_jato
            largura_atual = largura_base * (1 - part["dist"] * 0.6)
            x = CENTRO[0] + part["desvio"] * part["dist"] * 0.4
            y = CENTRO[1] + direcao * dist_px

            brilho = 255 - int(150 * part["dist"])
            cor_part = (brilho, brilho, 255)
            pygame.draw.circle(tela, cor_part, (int(x), int(y)), max(1, int(3 - part["dist"] * 2)))

        # Rotulo
        rotulo = fonte_pequena.render("RAIO GAMA", True, AZUL_JATO)
        pos_rotulo = (ponta[0] - rotulo.get_width() // 2, ponta[1] - 18 if direcao < 0 else ponta[1] + 4)
        tela.blit(rotulo, pos_rotulo)


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
            elif botao_gas_mais.collidepoint(evento.pos):
                gas = min(100, gas + 5)
            elif botao_gas_menos.collidepoint(evento.pos):
                gas = max(0, gas - 5)

    ativo_quasar, luminosidade, status, cor_status = calcular_estado(massa, gas)
    texto_comparacao = comparacao_real(luminosidade, ativo_quasar)

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    # Estrelas com leve piscada
    for (ex, ey, tam, fase) in estrelas:
        brilho = int(120 + 100 * math.sin(tempo * 0.001 * fase + ex))
        brilho = max(60, min(255, brilho))
        pygame.draw.circle(tela, (brilho, brilho, brilho), (ex, ey), tam)

    # Flash geral de tela quando quasar hiperluminoso
    if ativo_quasar and luminosidade > 80:
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pulso = int(20 + 15 * math.sin(tempo * 0.006))
        overlay.fill((120, 90, 200, pulso))
        tela.blit(overlay, (0, 0))

    # Painel esquerdo
    pygame.draw.rect(tela, PAINEL_BG, (0, 0, 300, ALTURA))
    tela.blit(fonte_titulo.render("ASCENSAO DE", True, BRANCO), (30, 22))
    tela.blit(fonte_titulo.render("UM QUASAR", True, ROXO_JATO), (30, 54))

    # Controles de massa
    tela.blit(fonte_label.render("MASSA", True, CINZA_CLARO), (40, 100))
    desenhar_botao(botao_massa_menos, "-", botao_massa_menos.collidepoint(mouse_pos))
    desenhar_botao(botao_massa_mais, "+", botao_massa_mais.collidepoint(mouse_pos))
    desenhar_barra(95, 138, 115, 26, massa, LARANJA)
    tela.blit(fonte_texto.render(f"{massa}/100", True, BRANCO), (100, 143))

    # Controles de gas
    tela.blit(fonte_label.render("QUANTIDADE DE GAS", True, CINZA_CLARO), (40, 215))
    desenhar_botao(botao_gas_menos, "-", botao_gas_menos.collidepoint(mouse_pos))
    desenhar_botao(botao_gas_mais, "+", botao_gas_mais.collidepoint(mouse_pos))
    desenhar_barra(95, 253, 115, 26, gas, AZUL_JATO)
    tela.blit(fonte_texto.render(f"{gas}/100", True, BRANCO), (100, 258))

    # Status
    pygame.draw.line(tela, CINZA, (30, 310), (270, 310), 1)
    tela.blit(fonte_label.render("STATUS:", True, CINZA_CLARO), (30, 325))

    # quebra de linha simples pro status
    palavras = status.split(" ")
    linha_atual = ""
    linhas = []
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        if fonte_status.size(teste)[0] > 250:
            linhas.append(linha_atual)
            linha_atual = palavra
        else:
            linha_atual = teste
    linhas.append(linha_atual)
    y_status = 355
    for linha in linhas:
        tela.blit(fonte_status.render(linha, True, cor_status), (30, y_status))
        y_status += 30

    y_status += 10
    tela.blit(fonte_pequena.render(f"Luminosidade: {luminosidade:.1f} / 100", True, CINZA_CLARO), (30, y_status))
    y_status += 25

    tela.blit(fonte_pequena.render("Comparavel a:", True, AMARELO), (30, y_status))
    y_status += 20
    palavras = texto_comparacao.split(" ")
    linha_atual = ""
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        if fonte_pequena.size(teste)[0] > 250:
            tela.blit(fonte_pequena.render(linha_atual, True, BRANCO), (30, y_status))
            y_status += 18
            linha_atual = palavra
        else:
            linha_atual = teste
    tela.blit(fonte_pequena.render(linha_atual, True, BRANCO), (30, y_status))

    if not ativo_quasar:
        y_status += 30
        dica = fonte_pequena.render(f"Dica: massa e gas >= {LIMIAR_MASSA_QUASAR}", True, CINZA)
        dica2 = fonte_pequena.render("para acender o quasar.", True, CINZA)
        tela.blit(dica, (30, y_status))
        tela.blit(dica2, (30, y_status + 18))

    # -------------------- SISTEMA (buraco negro / disco / jatos) --------------------
    raio_bh = 22 + massa * 0.35
    raio_disco = raio_bh + 25 + gas * 0.9
    intensidade = luminosidade if ativo_quasar else gas * 0.3

    # jatos atras do disco/buraco (desenhados primeiro se ativo)
    if ativo_quasar:
        desenhar_jatos(luminosidade, raio_bh)

    desenhar_disco(raio_bh, raio_disco, intensidade, 0.01)
    desenhar_buraco_negro(raio_bh)

    # Rodape
    rodape = fonte_pequena.render(
        "Simulacao ilustrativa - representa conceitos gerais de nucleos ativos e quasares.",
        True, (100, 105, 120)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 28))

    pygame.display.flip()

pygame.quit()
sys.exit()
