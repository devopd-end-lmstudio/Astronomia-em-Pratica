import pygame
import random
import math
import sys
from collections import deque

# ----------------------------------------------------------------------
# Configurações gerais
# ----------------------------------------------------------------------
WIDTH, HEIGHT = 1100, 800
MAIN_H = 620               # altura da área principal (onde fica a estrela)
CURVE_H = HEIGHT - MAIN_H  # altura do painel da curva de luz
FPS = 60

STAR_POS = pygame.Vector2(WIDTH // 2, MAIN_H // 2)
STAR_RADIUS = 16

BLACK = (5, 5, 10)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulacao de Pulsar")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
font_big = pygame.font.SysFont("consolas", 26, bold=True)


class EstrelaFundo:
    __slots__ = ("pos", "size", "brilho_base", "fase")

    def __init__(self):
        self.pos = (random.uniform(0, WIDTH), random.uniform(0, MAIN_H))
        self.size = random.choice([1, 1, 1, 2])
        self.brilho_base = random.randint(80, 200)
        self.fase = random.uniform(0, math.tau)

    def desenhar(self, surf, t):
        cintilar = 0.7 + 0.3 * math.sin(t * 2 + self.fase)
        b = int(self.brilho_base * cintilar)
        pygame.draw.circle(surf, (b, b, b), (int(self.pos[0]), int(self.pos[1])), self.size)


def desenhar_feixe(surface, centro, angulo_graus, meia_largura_graus, raio_max, cor, camadas=16):
    """Desenha um feixe (cone) saindo da estrela, mais brilhante perto do centro
    e esmaecendo conforme a distancia aumenta."""
    for i in range(camadas, 0, -1):
        frac = i / camadas
        r = raio_max * frac
        alpha = int(150 * (1 - frac) ** 1.4)
        if alpha <= 0:
            continue
        pontos = [centro]
        passos = 10
        for s in range(passos + 1):
            a = math.radians(angulo_graus - meia_largura_graus + (2 * meia_largura_graus) * (s / passos))
            pontos.append(centro + pygame.Vector2(math.cos(a), math.sin(a)) * r)
        c = (*cor, alpha)
        pygame.draw.polygon(surface, c, [(p.x, p.y) for p in pontos])


def diferenca_angular(a, b):
    """Menor diferenca angular entre dois angulos em graus (0 a 180)."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def main():
    periodo_rotacao = 1.6          # segundos por rotação completa (começa devagar, tipo farol)
    periodo_min, periodo_max = 0.12, 4.0
    meia_largura_graus = 14.0
    meia_largura_min, meia_largura_max = 4.0, 35.0

    rotacao_graus = 0.0
    t = 0.0
    pausado = False

    pos_detector = pygame.Vector2(WIDTH - 60, MAIN_H // 2)

    estrelas = [EstrelaFundo() for _ in range(180)]

    tamanho_curva = 500
    curva_luz = deque([0.0] * tamanho_curva, maxlen=tamanho_curva)

    contador_pulsos = 0
    estava_acima_limiar = False
    limiar = 0.5

    flashes = []  # [pos, frame, intensidade]

    superficie_feixes = pygame.Surface((WIDTH, MAIN_H), pygame.SRCALPHA)

    rodando = True
    while rodando:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 30)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_SPACE:
                    pausado = not pausado
                elif evento.key == pygame.K_r:
                    rotacao_graus = 0.0
                    periodo_rotacao = 1.6
                    meia_largura_graus = 14.0
                    curva_luz = deque([0.0] * tamanho_curva, maxlen=tamanho_curva)
                    contador_pulsos = 0
                    flashes.clear()
                elif evento.key == pygame.K_UP:
                    periodo_rotacao = max(periodo_min, periodo_rotacao * 0.85)
                elif evento.key == pygame.K_DOWN:
                    periodo_rotacao = min(periodo_max, periodo_rotacao / 0.85)
                elif evento.key == pygame.K_LEFT:
                    meia_largura_graus = max(meia_largura_min, meia_largura_graus - 1.5)
                elif evento.key == pygame.K_RIGHT:
                    meia_largura_graus = min(meia_largura_max, meia_largura_graus + 1.5)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mx, my = pygame.mouse.get_pos()
                if my < MAIN_H:
                    pos_detector = pygame.Vector2(mx, my)

        if not pausado:
            t += dt
            velocidade_angular = 360.0 / periodo_rotacao  # graus por segundo
            rotacao_graus = (rotacao_graus + velocidade_angular * dt) % 360

            angulo_feixe1 = rotacao_graus
            angulo_feixe2 = (rotacao_graus + 180) % 360

            para_detector = pos_detector - STAR_POS
            angulo_detector = math.degrees(math.atan2(para_detector.y, para_detector.x)) % 360

            d1 = diferenca_angular(angulo_feixe1, angulo_detector)
            d2 = diferenca_angular(angulo_feixe2, angulo_detector)
            menor_d = min(d1, d2)

            # perfil de pulso tipo gaussiano, cai suavemente conforme o feixe
            # se afasta da linha de visão
            sigma = meia_largura_graus * 0.55
            intensidade = math.exp(-(menor_d ** 2) / (2 * sigma ** 2))
            if intensidade < 0.02:
                intensidade = 0.0

            curva_luz.append(intensidade)

            esta_acima = intensidade > limiar
            if esta_acima and not estava_acima_limiar:
                contador_pulsos += 1
                flashes.append([pos_detector.copy(), 0, intensidade])
            estava_acima_limiar = esta_acima

        # ---------------- desenho ----------------
        screen.fill(BLACK)

        for s in estrelas:
            s.desenhar(screen, t)

        # eixo de rotação (linha vertical pontilhada de referência)
        for y in range(0, MAIN_H, 12):
            pygame.draw.line(screen, (60, 60, 80), (STAR_POS.x, y), (STAR_POS.x, y + 6), 1)

        # feixes (desenhados numa superfície separada com alpha, depois somados)
        superficie_feixes.fill((0, 0, 0, 0))
        raio_max = math.hypot(WIDTH, MAIN_H)
        desenhar_feixe(superficie_feixes, STAR_POS, angulo_feixe1 if not pausado else rotacao_graus,
                       meia_largura_graus, raio_max, (140, 200, 255))
        desenhar_feixe(superficie_feixes, STAR_POS, (angulo_feixe1 + 180) % 360 if not pausado else (rotacao_graus + 180) % 360,
                       meia_largura_graus, raio_max, (200, 160, 255))
        screen.blit(superficie_feixes, (0, 0), special_flags=pygame.BLEND_ADD)

        # brilho ao redor da estrela
        for i in range(6, 0, -1):
            r = STAR_RADIUS + i * 4
            alpha = int(12 * (7 - i))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (180, 210, 255, alpha), (r, r), r)
            screen.blit(s, (STAR_POS.x - r, STAR_POS.y - r), special_flags=pygame.BLEND_ADD)

        # a estrela de nêutrons em si
        pygame.draw.circle(screen, (230, 240, 255), (int(STAR_POS.x), int(STAR_POS.y)), STAR_RADIUS)
        pygame.draw.circle(screen, WHITE, (int(STAR_POS.x), int(STAR_POS.y)), STAR_RADIUS, 2)

        # detector ("a Terra")
        pygame.draw.circle(screen, (90, 220, 130), (int(pos_detector.x), int(pos_detector.y)), 6)
        pygame.draw.circle(screen, WHITE, (int(pos_detector.x), int(pos_detector.y)), 6, 1)
        rotulo = font.render("detector", True, (150, 230, 170))
        screen.blit(rotulo, (pos_detector.x + 10, pos_detector.y - 10))

        # flashes no detector quando o pulso chega
        novos_flashes = []
        for pos, frame, inten in flashes:
            frame += 1
            if frame < 14:
                r = int(8 + frame * 2.2 * inten)
                alpha = max(0, int(200 * (1 - frame / 14)))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, alpha), (r, r), r)
                screen.blit(s, (pos.x - r, pos.y - r), special_flags=pygame.BLEND_ADD)
                novos_flashes.append([pos, frame, inten])
        flashes = novos_flashes

        # ---------------- painel da curva de luz ----------------
        topo_painel = MAIN_H
        pygame.draw.rect(screen, (12, 12, 20), (0, topo_painel, WIDTH, CURVE_H))
        pygame.draw.line(screen, (80, 80, 100), (0, topo_painel), (WIDTH, topo_painel), 2)

        grafico_esq = 60
        grafico_dir = WIDTH - 20
        grafico_larg = grafico_dir - grafico_esq
        grafico_topo = topo_painel + 15
        grafico_alt = CURVE_H - 45

        # grade
        for gy in range(5):
            y = grafico_topo + grafico_alt * gy / 4
            pygame.draw.line(screen, (40, 40, 55), (grafico_esq, y), (grafico_dir, y), 1)

        pts = list(curva_luz)
        n = len(pts)
        passo_x = grafico_larg / max(1, n - 1)
        pontos_poligono = []
        for i, v in enumerate(pts):
            x = grafico_esq + i * passo_x
            y = grafico_topo + grafico_alt - v * grafico_alt
            pontos_poligono.append((x, y))
        if len(pontos_poligono) > 1:
            pygame.draw.lines(screen, (120, 230, 255), False, pontos_poligono, 2)

        # eixo e legendas
        rotulo_eixo = font.render("Curva de luz (intensidade detectada)", True, (200, 200, 220))
        screen.blit(rotulo_eixo, (grafico_esq, topo_painel + CURVE_H - 22))

        # ---------------- HUD ----------------
        freq_hz = 1.0 / periodo_rotacao
        linhas_hud = [
            f"Periodo de rotacao: {periodo_rotacao*1000:.1f} ms   (frequencia: {freq_hz:.2f} Hz)",
            f"Largura do feixe: {meia_largura_graus:.1f} graus",
            f"Pulsos detectados: {contador_pulsos}",
            "SETAS cima/baixo: velocidade | esquerda/direita: largura do feixe",
            "Clique esquerdo: mover detector | R: reiniciar | ESPACO: pausa | ESC: sair",
        ]
        for i, linha in enumerate(linhas_hud):
            txt = font.render(linha, True, (210, 210, 230))
            screen.blit(txt, (12, 10 + i * 20))

        if pausado:
            txt = font_big.render("PAUSADO", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
