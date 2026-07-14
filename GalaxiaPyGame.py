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
pygame.display.set_caption("Formacao de Galaxias")
relogio = pygame.time.Clock()

PRETO = (5, 5, 10)
BRANCO = (245, 245, 250)
CINZA = (90, 95, 110)
CINZA_CLARO = (160, 165, 180)
AMARELO = (255, 215, 120)
LARANJA = (255, 150, 60)
VERMELHO = (220, 90, 70)
AZUL = (130, 180, 255)
ROXO = (170, 120, 230)
ROSA = (255, 140, 200)
PAINEL_BG = (16, 18, 28)

fonte_titulo = pygame.font.SysFont("arial", 27, bold=True)
fonte_label = pygame.font.SysFont("arial", 18, bold=True)
fonte_texto = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 14)
fonte_status = pygame.font.SysFont("arial", 20, bold=True)

CENTRO = (660, 400)

# ----------------------------------------------------------------------
# ESTADO DO SISTEMA
# ----------------------------------------------------------------------
massa = 10
rotacao = 10
gas = 50

massa_suave = float(massa)
rotacao_suave = float(rotacao)
gas_suave = float(gas)

LIMIAR_MASSA_MIN = 15         # minimo para comecar a colapsar
LIMIAR_ROTACAO_DISCO = 40     # acima disso, achata em disco (espiral); abaixo, esferoidal
LIMIAR_GAS_FORMACAO = 30      # acima disso, formacao estelar ativa (braços azuis)
LIMIAR_GAS_STARBURST = 70     # muito gas = surto intenso de formacao estelar

tempo = 0
rotacao_fase = 0.0

# ----------------------------------------------------------------------
# PARTICULAS PRE-GERADAS (padroes fixos, reaproveitados a cada frame)
# ----------------------------------------------------------------------
NUM_NUVEM = 260
particulas_nuvem = [{
    "angulo": random.uniform(0, math.tau),
    "fator_raio": random.uniform(0.3, 1.0),
    "vel": random.uniform(0.3, 1.0),
    "tamanho": random.uniform(1, 2.4),
} for _ in range(NUM_NUVEM)]

NUM_ESFEROIDE = 320
particulas_esferoide = [{
    "angulo": random.uniform(0, math.tau),
    "fator_raio": random.random() ** 1.8,   # concentra mais estrelas perto do centro
    "tamanho": random.uniform(1, 2.2),
} for _ in range(NUM_ESFEROIDE)]

NUM_CLUMPS_ANA = 5
CLUMPS_ANA = [(random.uniform(-0.5, 0.5), random.uniform(-0.4, 0.4)) for _ in range(NUM_CLUMPS_ANA)]
particulas_ana = [{
    "clump": random.randrange(NUM_CLUMPS_ANA),
    "offset_x": random.uniform(-0.22, 0.22),
    "offset_y": random.uniform(-0.22, 0.22),
    "tamanho": random.uniform(1, 2.4),
} for _ in range(260)]

NUM_BRACOS = 4
PARTICULAS_POR_BRACO = 130
VOLTAS_BRACO = 2.4 * math.tau
particulas_espiral = []
for k in range(NUM_BRACOS):
    angulo_base = k * (math.tau / NUM_BRACOS)
    for i in range(PARTICULAS_POR_BRACO):
        t = i / PARTICULAS_POR_BRACO
        particulas_espiral.append({
            "angulo_base": angulo_base,
            "t": t,
            "offset": random.uniform(-0.05, 0.05),
            "offset_raio": random.uniform(-0.04, 0.04),
            "tamanho": random.uniform(1, 2.6),
            "hii": random.random() < 0.12,  # regiao de formacao estelar (rosa)
        })

NUM_BULBO = 90
particulas_bulbo = [{
    "angulo": random.uniform(0, math.tau),
    "fator_raio": random.random() ** 2,
    "tamanho": random.uniform(1, 2.2),
} for _ in range(NUM_BULBO)]

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

botao_massa_menos = criar_botao(40, 122)
botao_massa_mais = criar_botao(220, 122)

botao_rot_menos = criar_botao(40, 225)
botao_rot_mais = criar_botao(220, 225)

botao_gas_menos = criar_botao(40, 328)
botao_gas_mais = criar_botao(220, 328)


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
def calcular_estado(massa, rotacao, gas):
    if massa < LIMIAR_MASSA_MIN:
        return "nuvem"

    if rotacao < LIMIAR_ROTACAO_DISCO:
        # colapso esferoidal
        if gas < LIMIAR_GAS_FORMACAO:
            return "eliptica"
        else:
            return "ana_irregular"
    else:
        # colapso em disco
        if gas < LIMIAR_GAS_FORMACAO:
            return "lenticular"
        elif gas < LIMIAR_GAS_STARBURST:
            return "espiral"
        else:
            return "espiral_starburst"


INFO_TIPOS = {
    "nuvem": ("Nuvem Primordial Dispersa", CINZA_CLARO,
               "Como uma nuvem de gas e materia escura logo apos o Big Bang, antes de qualquer galaxia se formar."),
    "eliptica": ("Galaxia Eliptica", AMARELO,
                  "Parecida com M87, uma galaxia eliptica gigante no aglomerado de Virgem, cheia de estrelas velhas."),
    "ana_irregular": ("Galaxia Ana Irregular", AZUL,
                        "Semelhante a Grande Nuvem de Magalhaes, pequena e irregular, mas com formacao estelar ativa."),
    "lenticular": ("Galaxia Lenticular (S0)", (200, 190, 160),
                     "Comparavel a NGC 5866, um disco achatado que ja gastou quase todo o seu gas."),
    "espiral": ("Galaxia Espiral", AZUL,
                 "Muito parecida com a Via Lactea ou a Galaxia de Andromeda."),
    "espiral_starburst": ("Espiral em Surto de Formacao Estelar", ROSA,
                            "Rivaliza com a Galaxia do Charuto (M82), famosa por seu intenso surto de formacao estelar."),
}


# ----------------------------------------------------------------------
# DESENHO
# ----------------------------------------------------------------------
def raio_base(massa_v):
    return 40 + massa_v * 2.0


def cor_por_gas(gas_v, cor_pouco_gas, cor_muito_gas):
    t = max(0, min(1, gas_v / 100))
    return tuple(int(cor_pouco_gas[i] + (cor_muito_gas[i] - cor_pouco_gas[i]) * t) for i in range(3))


def desenhar_nuvem(massa_v, fase):
    raio_alvo = 260
    num_visiveis = int(NUM_NUVEM * max(massa_v, 4) / 100)
    for p in particulas_nuvem[:num_visiveis]:
        p["angulo"] += 0.0015 * p["vel"]
        r = raio_alvo * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"])
        y = CENTRO[1] + r * math.sin(p["angulo"])
        pygame.draw.circle(tela, (140, 130, 160), (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_esferoide(massa_v, gas_v, tipo, fase):
    raio = raio_base(massa_v)
    achatamento = 0.85

    if tipo == "eliptica":
        cor_base = cor_por_gas(gas_v, (235, 205, 140), (255, 225, 170))
    else:
        cor_base = cor_por_gas(gas_v, (150, 180, 230), (140, 200, 255))

    lista = particulas_esferoide if tipo == "eliptica" else particulas_ana

    if tipo == "eliptica":
        for p in lista:
            p["angulo"] += 0.0008
            r = raio * p["fator_raio"]
            x = CENTRO[0] + r * math.cos(p["angulo"])
            y = CENTRO[1] + r * math.sin(p["angulo"]) * achatamento
            escurecimento = 0.55 + 0.45 * (1 - p["fator_raio"])
            cor = tuple(int(c * escurecimento) for c in cor_base)
            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))
    else:
        for p in lista:
            cx_clump, cy_clump = CLUMPS_ANA[p["clump"]]
            x = CENTRO[0] + (cx_clump + p["offset_x"]) * raio * 1.6
            y = CENTRO[1] + (cy_clump + p["offset_y"]) * raio * 1.6 * achatamento
            cor = cor_base if random.random() > 0.15 else (255, 255, 255)
            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))


def desenhar_disco(massa_v, gas_v, tipo, fase):
    raio = raio_base(massa_v)
    achatamento = 0.42

    if tipo == "lenticular":
        cor_disco = cor_por_gas(gas_v, (215, 200, 170), (225, 210, 185))
        for p in particulas_esferoide:
            r = raio * p["fator_raio"] * 1.3
            ang = p["angulo"]
            x = CENTRO[0] + r * math.cos(ang)
            y = CENTRO[1] + r * math.sin(ang) * achatamento
            escurecimento = 0.55 + 0.4 * (1 - p["fator_raio"])
            cor = tuple(int(c * escurecimento) for c in cor_disco)
            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))
    else:
        # bracos espirais
        cor_fria = (255, 225, 170)
        cor_ativa = (150, 190, 255) if tipo == "espiral" else (200, 150, 255)
        for p in particulas_espiral:
            t = p["t"]
            ang = p["angulo_base"] + t * VOLTAS_BRACO + fase + p["offset"]
            r = (0.12 + t * 0.9 + p["offset_raio"]) * raio * 1.7
            x = CENTRO[0] + r * math.cos(ang)
            y = CENTRO[1] + r * math.sin(ang) * achatamento

            if p["hii"] and gas_v >= LIMIAR_GAS_FORMACAO:
                cor = ROSA if tipo == "espiral_starburst" else (255, 190, 220)
            else:
                brilho_t = max(0, min(1, gas_v / 100))
                cor = tuple(int(cor_fria[i] + (cor_ativa[i] - cor_fria[i]) * brilho_t) for i in range(3))

            pygame.draw.circle(tela, cor, (int(x), int(y)), max(1, int(p["tamanho"])))

    # bojo central (bulge) - presente em todo disco
    for p in particulas_bulbo:
        r = raio * 0.22 * p["fator_raio"]
        x = CENTRO[0] + r * math.cos(p["angulo"] + fase * 0.4)
        y = CENTRO[1] + r * math.sin(p["angulo"] + fase * 0.4) * achatamento
        pygame.draw.circle(tela, (255, 235, 190), (int(x), int(y)), max(1, int(p["tamanho"])))

    # buraco negro supermassivo central (so um pontinho escuro sutil)
    pygame.draw.circle(tela, (10, 8, 5), CENTRO, 3)


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
            elif botao_rot_mais.collidepoint(evento.pos):
                rotacao = min(100, rotacao + 5)
            elif botao_rot_menos.collidepoint(evento.pos):
                rotacao = max(0, rotacao - 5)
            elif botao_gas_mais.collidepoint(evento.pos):
                gas = min(100, gas + 5)
            elif botao_gas_menos.collidepoint(evento.pos):
                gas = max(0, gas - 5)

    massa_suave += (massa - massa_suave) * 0.08
    rotacao_suave += (rotacao - rotacao_suave) * 0.08
    gas_suave += (gas - gas_suave) * 0.08

    rotacao_fase += 0.0006 * (1 + rotacao_suave / 40)

    estagio = calcular_estado(massa, rotacao, gas)

    # -------------------- DESENHO --------------------
    tela.fill(PRETO)

    for (ex, ey, tam, fase_estrela) in estrelas_fundo:
        brilho = int(120 + 100 * math.sin(tempo * 0.001 * fase_estrela + ex))
        brilho = max(60, min(255, brilho))
        pygame.draw.circle(tela, (brilho, brilho, brilho), (ex, ey), tam)

    # Painel esquerdo
    pygame.draw.rect(tela, PAINEL_BG, (0, 0, 300, ALTURA))
    tela.blit(fonte_titulo.render("FORMACAO DE", True, BRANCO), (30, 20))
    tela.blit(fonte_titulo.render("GALAXIAS", True, ROXO), (30, 50))

    # MASSA
    tela.blit(fonte_label.render("MASSA", True, CINZA_CLARO), (40, 95))
    desenhar_botao(botao_massa_menos, "-", botao_massa_menos.collidepoint(mouse_pos), AMARELO)
    desenhar_botao(botao_massa_mais, "+", botao_massa_mais.collidepoint(mouse_pos), AMARELO)
    desenhar_barra(95, 130, 115, 24, massa, AMARELO)
    tela.blit(fonte_texto.render(f"{massa}/100", True, BRANCO), (100, 134))

    # ROTACAO
    tela.blit(fonte_label.render("ROTACAO", True, CINZA_CLARO), (40, 198))
    desenhar_botao(botao_rot_menos, "-", botao_rot_menos.collidepoint(mouse_pos), AZUL)
    desenhar_botao(botao_rot_mais, "+", botao_rot_mais.collidepoint(mouse_pos), AZUL)
    desenhar_barra(95, 233, 115, 24, rotacao, AZUL)
    tela.blit(fonte_texto.render(f"{rotacao}/100", True, BRANCO), (100, 237))

    # GAS
    tela.blit(fonte_label.render("GAS", True, CINZA_CLARO), (40, 301))
    desenhar_botao(botao_gas_menos, "-", botao_gas_menos.collidepoint(mouse_pos), ROSA)
    desenhar_botao(botao_gas_mais, "+", botao_gas_mais.collidepoint(mouse_pos), ROSA)
    desenhar_barra(95, 336, 115, 24, gas, ROSA)
    tela.blit(fonte_texto.render(f"{gas}/100", True, BRANCO), (100, 340))

    # Status
    pygame.draw.line(tela, CINZA, (30, 385), (270, 385), 1)
    tela.blit(fonte_label.render("STATUS:", True, CINZA_CLARO), (30, 398))

    nome_status, cor_status, comparacao = INFO_TIPOS[estagio]
    y_status = 425
    for linha in texto_em_linhas(nome_status, fonte_status, 250):
        tela.blit(fonte_status.render(linha, True, cor_status), (30, y_status))
        y_status += 26

    y_status += 8
    tela.blit(fonte_pequena.render("Comparavel a:", True, AMARELO), (30, y_status))
    y_status += 20
    for linha in texto_em_linhas(comparacao, fonte_pequena, 250):
        tela.blit(fonte_pequena.render(linha, True, BRANCO), (30, y_status))
        y_status += 18

    if estagio == "nuvem":
        y_status += 20
        dica = f"Dica: junte pelo menos {LIMIAR_MASSA_MIN} de massa para comecar o colapso."
    elif estagio in ("eliptica", "lenticular"):
        y_status += 20
        dica = f"Dica: gas >= {LIMIAR_GAS_FORMACAO} para acender formacao estelar ativa."
    else:
        dica = None

    if dica:
        for linha in texto_em_linhas(dica, fonte_pequena, 250):
            tela.blit(fonte_pequena.render(linha, True, CINZA), (30, y_status))
            y_status += 16

    # -------------------- VISUALIZACAO CENTRAL --------------------
    if estagio == "nuvem":
        desenhar_nuvem(massa_suave, rotacao_fase)
    elif estagio in ("eliptica", "ana_irregular"):
        desenhar_esferoide(massa_suave, gas_suave, estagio, rotacao_fase)
    else:
        desenhar_disco(massa_suave, gas_suave, estagio, rotacao_fase)

    rodape = fonte_pequena.render(
        "Simulacao ilustrativa - representa de forma simplificada o colapso e a formacao de galaxias.",
        True, (100, 105, 120)
    )
    tela.blit(rodape, (300 + (LARGURA - 300 - rodape.get_width()) // 2, ALTURA - 26))

    pygame.display.flip()

pygame.quit()
sys.exit()
