import pygame
import random
import math
import sys

# ----------------------------------------------------------------------
# Configurações gerais
# ----------------------------------------------------------------------
WIDTH, HEIGHT = 1100, 750
FPS = 60

G = 1200.0          # constante gravitacional "de jogo"
BH_MASS = 9000.0    # massa inicial do buraco negro
BH_POS = pygame.Vector2(WIDTH // 2, HEIGHT // 2)

MAX_PARTICLES = 900
STAR_COUNT = 220

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulacao de Buraco Negro Ber-618*")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
font_big = pygame.font.SysFont("consolas", 28, bold=True)


def schwarzschild_radius(mass):
    """Raio do horizonte de eventos (escala artistica, nao fisica real)."""
    return max(14.0, math.sqrt(mass) * 0.55)


def temp_color(speed, min_s=0, max_s=900):
    """Converte velocidade em uma cor tipo 'corpo negro' (vermelho -> branco -> azul)."""
    t = max(0.0, min(1.0, (speed - min_s) / (max_s - min_s)))
    if t < 0.5:
        # vermelho escuro -> laranja/amarelo
        k = t / 0.5
        r = 180 + int(75 * k)
        g = int(60 + 150 * k)
        b = int(20 + 40 * k)
    else:
        # amarelo -> branco -> azul claro
        k = (t - 0.5) / 0.5
        r = int(255 - 80 * k)
        g = int(210 - 30 * k)
        b = int(60 + 195 * k)
    return (min(255, r), min(255, g), min(255, b))


class Particle:
    __slots__ = ("pos", "vel", "trail", "alive", "mass")

    def __init__(self, pos, vel, mass=1.0):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.trail = []
        self.alive = True
        self.mass = mass

    def update(self, dt, bh_mass, bh_radius):
        to_center = BH_POS - self.pos
        dist = to_center.length()

        if dist < bh_radius:
            self.alive = False
            return

        # gravidade newtoniana
        force_mag = G * bh_mass / (dist * dist)
        accel = to_center.normalize() * force_mag
        self.vel += accel * dt
        self.pos += self.vel * dt

        # rastro
        self.trail.append(self.pos.copy())
        if len(self.trail) > 14:
            self.trail.pop(0)

        # se saiu muito da tela, mata a partícula
        if not (-200 <= self.pos.x <= WIDTH + 200 and -200 <= self.pos.y <= HEIGHT + 200):
            self.alive = False

    def draw(self, surf, bh_radius):
        dist = (BH_POS - self.pos).length()
        speed = self.vel.length()
        color = temp_color(speed)

        # espaguetificação: perto do horizonte, estica o traço radialmente
        near = max(0.0, 1.0 - (dist - bh_radius) / (bh_radius * 3))

        # desenha rastro (disco de acreção)
        n = len(self.trail)
        for i, p in enumerate(self.trail):
            alpha_k = i / max(1, n)
            c = (
                int(color[0] * alpha_k),
                int(color[1] * alpha_k),
                int(color[2] * alpha_k),
            )
            r = max(1, int(2 * alpha_k))
            pygame.draw.circle(surf, c, (int(p.x), int(p.y)), r)

        radius = max(1, int(2 + near * 3))
        pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), radius)


class BackgroundStar:
    """Estrela de fundo estatica, distorcida pela 'lente gravitacional'."""

    __slots__ = ("base_pos", "size", "brightness")

    def __init__(self):
        self.base_pos = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.size = random.choice([1, 1, 1, 2])
        self.brightness = random.randint(120, 255)

    def draw(self, surf, bh_radius, lens_strength):
        to_center = self.base_pos - BH_POS
        dist = to_center.length()
        if dist < 1:
            return
        # deslocamento de "lente": quanto mais perto do horizonte, mais desvia
        bend = lens_strength * (bh_radius ** 1.6) / (dist ** 1.2)
        bend = min(bend, dist - bh_radius * 1.02) if dist > bh_radius * 1.02 else 0
        if bend <= 0:
            return
        display_pos = self.base_pos - to_center.normalize() * bend

        c = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(surf, c, (int(display_pos.x), int(display_pos.y)), self.size)


def spawn_ring_particles(n, bh_radius):
    """Cria particulas em orbita ao redor do buraco negro para formar um disco inicial."""
    particles = []
    for _ in range(n):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(bh_radius * 2.2, bh_radius * 7)
        pos = BH_POS + pygame.Vector2(math.cos(angle), math.sin(angle)) * radius
        # velocidade orbital aproximada (v = sqrt(G*M/r)), tangencial
        orbital_speed = math.sqrt(G * BH_MASS / radius) * random.uniform(0.85, 1.05)
        tangent = pygame.Vector2(-math.sin(angle), math.cos(angle))
        vel = tangent * orbital_speed
        particles.append(Particle(pos, vel))
    return particles


def make_flash(flashes, pos):
    flashes.append([pygame.Vector2(pos), 0])


def main():
    global BH_MASS

    bh_radius = schwarzschild_radius(BH_MASS)
    particles = spawn_ring_particles(260, bh_radius)
    stars = [BackgroundStar() for _ in range(STAR_COUNT)]
    flashes = []  # [pos, frame_idx]

    paused = False
    mouse_down_left = False
    mouse_down_right = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 30)  # evita saltos grandes

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    BH_MASS = 9000.0
                    bh_radius = schwarzschild_radius(BH_MASS)
                    particles = spawn_ring_particles(260, bh_radius)
                    flashes.clear()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    BH_MASS *= 1.15
                    bh_radius = schwarzschild_radius(BH_MASS)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    BH_MASS = max(500.0, BH_MASS * 0.87)
                    bh_radius = schwarzschild_radius(BH_MASS)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down_left = True
                elif event.button == 3:
                    mouse_down_right = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down_left = False
                elif event.button == 3:
                    mouse_down_right = False

        if not paused:
            mx, my = pygame.mouse.get_pos()

            if mouse_down_left and len(particles) < MAX_PARTICLES:
                for _ in range(3):
                    jitter = pygame.Vector2(random.uniform(-6, 6), random.uniform(-6, 6))
                    vel = pygame.Vector2(random.uniform(-40, 40), random.uniform(-40, 40))
                    particles.append(Particle((mx, my) + jitter, vel))

            if mouse_down_right and len(particles) < MAX_PARTICLES:
                to_center = BH_POS - pygame.Vector2(mx, my)
                dist = max(1, to_center.length())
                tangent = pygame.Vector2(-to_center.y, to_center.x).normalize()
                orb_speed = math.sqrt(G * BH_MASS / dist)
                particles.append(Particle((mx, my), tangent * orb_speed))

            # atualiza partículas
            for p in particles:
                p.update(dt, BH_MASS, bh_radius)
                if not p.alive and (BH_POS - p.pos).length() < bh_radius * 1.5:
                    make_flash(flashes, p.pos)

            particles = [p for p in particles if p.alive]

        # ---------------- desenho ----------------
        screen.fill(BLACK)

        # leve nebulosa de fundo
        for star in stars:
            star.draw(screen, bh_radius, lens_strength=1400.0)

        for p in particles:
            p.draw(screen, bh_radius)

        # flashes de partículas engolidas
        new_flashes = []
        for pos, frame in flashes:
            frame += 1
            if frame < 10:
                alpha_r = 6 + frame
                color = (255, 255, 255)
                s = pygame.Surface((alpha_r * 2, alpha_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    s, (*color, max(0, 180 - frame * 18)), (alpha_r, alpha_r), alpha_r
                )
                screen.blit(s, (pos.x - alpha_r, pos.y - alpha_r))
                new_flashes.append([pos, frame])
        flashes = new_flashes

        # horizonte de eventos (círculo preto sólido com borda suave)
        glow_layers = 5
        for i in range(glow_layers, 0, -1):
            r = int(bh_radius + i * 6)
            alpha = int(30 * (glow_layers - i + 1) / glow_layers)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 140, 60, alpha), (r, r), r)
            screen.blit(s, (BH_POS.x - r, BH_POS.y - r))

        pygame.draw.circle(screen, BLACK, (int(BH_POS.x), int(BH_POS.y)), int(bh_radius))
        pygame.draw.circle(screen, (255, 200, 140), (int(BH_POS.x), int(BH_POS.y)), int(bh_radius), 2)

        # ---------------- HUD ----------------
        hud_lines = [
            f"Massa do Ber-618*: {BH_MASS:,.0f}".replace(",", "."),
            f"Raio de Schwarzschild: {bh_radius:.1f}px",
            f"Particulas: {len(particles)}/{MAX_PARTICLES}",
            "Clique esq: soltar particulas | Clique dir: particula em orbita",
            "+/- : massa | R: reiniciar | ESPACO: pausa | ESC: sair",
        ]
        for i, line in enumerate(hud_lines):
            txt = font.render(line, True, (200, 200, 220))
            screen.blit(txt, (12, 10 + i * 20))

        if paused:
            txt = font_big.render("PAUSADO", True, (255, 255, 255))
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
