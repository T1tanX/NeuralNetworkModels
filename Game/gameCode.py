import pygame
import random
import csv
import os
import sys

# ── Instellingen ──────────────────────────────────────────────────────────────
BREEDTE, HOOGTE = 400, 600
FPS = 60
CSV_BESTAND = "trainingsdata.csv"

# Kleuren
ACHTERGROND  = (10,  10,  26)
SPELER_KLEUR = (127, 119, 221)
SPELER_RAND  = (175, 169, 236)
TEKST_KLEUR  = (255, 255, 255)
ROOD         = (226,  75,  74)
GEEL         = (239, 159,  39)
BLAUW        = (133, 183, 235)
GROEN        = ( 93, 202, 165)
GRIJS        = ( 80,  80,  80)

STEEN_KLEUREN = [ROOD, GEEL, BLAUW, GROEN]

CSV_HEADER = [
    "speler_x_midden",
    "speler_x_links",
    "ruimte_rechts",
    "steen_x",
    "steen_y",
    "steen_snelheid",
    "relatief_verschil",
    "aantal_stenen",
    "score",
    "actie",          # -1 = links, 0 = stil, 1 = rechts
]

# ── Helperfuncties ─────────────────────────────────────────────────────────────

def schrijf_csv_header():
    """Maak het CSV-bestand aan met header als het nog niet bestaat."""
    if not os.path.exists(CSV_BESTAND):
        with open(CSV_BESTAND, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)


def sla_rij_op(rij: list):
    """Voeg één datarij toe aan het CSV-bestand."""
    with open(CSV_BESTAND, "a", newline="") as f:
        csv.writer(f).writerow(rij)


def dichtstbijzijnde_steen(speler_rect: pygame.Rect, stenen: list) -> dict | None:
    """Geef de steen terug die het dichtst bij de speler is (of None)."""
    if not stenen:
        return None
    sx = speler_rect.centerx
    sy = speler_rect.centery
    return min(stenen, key=lambda s: abs(s["rect"].centerx - sx) + abs(s["rect"].centery - sy))


def maak_rij(speler: pygame.Rect, stenen: list, score: int, actie: int) -> list:
    """Bouw één CSV-rij op basis van de huidige spelstaat."""
    dichtste = dichtstbijzijnde_steen(speler, stenen)

    steen_x       = dichtste["rect"].centerx  if dichtste else BREEDTE // 2
    steen_y       = dichtste["rect"].centery  if dichtste else -100
    steen_snelh   = round(dichtste["snelheid"], 2) if dichtste else 0.0
    rel_verschil  = steen_x - speler.centerx

    return [
        speler.centerx,
        speler.left,
        BREEDTE - speler.right,
        steen_x,
        steen_y,
        steen_snelh,
        rel_verschil,
        len(stenen),
        score,
        actie,
    ]


# ── Schermfuncties ─────────────────────────────────────────────────────────────

def teken_raster(scherm: pygame.Surface):
    for x in range(0, BREEDTE, 40):
        pygame.draw.line(scherm, (255, 255, 255, 15), (x, 0), (x, HOOGTE))
    for y in range(0, HOOGTE, 40):
        pygame.draw.line(scherm, (255, 255, 255, 15), (0, y), (BREEDTE, y))


def teken_speler(scherm: pygame.Surface, rect: pygame.Rect):
    pygame.draw.rect(scherm, SPELER_KLEUR, rect, border_radius=5)
    # Kleine antenne bovenop
    antenne_x = rect.centerx - 3
    pygame.draw.rect(scherm, SPELER_RAND, (antenne_x, rect.top - 8, 6, 8))


def teken_steen(scherm: pygame.Surface, steen: dict):
    pygame.draw.rect(scherm, steen["kleur"], steen["rect"], border_radius=4)


def teken_hud(scherm: pygame.Surface, font: pygame.font.Font, score: int,
              data_rijen: int, stenen: int):
    labels = [
        (f"Score: {score}",         (10, 10)),
        (f"Stenen: {stenen}",       (10, 32)),
        (f"Data: {data_rijen} rijen", (10, 54)),
    ]
    for tekst, pos in labels:
        scherm.blit(font.render(tekst, True, TEKST_KLEUR), pos)


def toon_startscherm(scherm: pygame.Surface, groot_font, klein_font):
    scherm.fill(ACHTERGROND)
    regels = [
        (groot_font, "STEEN ONTWIJKER", SPELER_RAND, HOOGTE // 2 - 80),
        (klein_font, "Beweeg: ← → of A / D",    TEKST_KLEUR, HOOGTE // 2 - 10),
        (klein_font, "Data wordt opgeslagen als:", GRIJS,      HOOGTE // 2 + 20),
        (klein_font, CSV_BESTAND,                  BLAUW,      HOOGTE // 2 + 44),
        (klein_font, "Druk op SPATIEBALK om te starten", GEEL, HOOGTE // 2 + 90),
    ]
    for font, tekst, kleur, y in regels:
        opp = font.render(tekst, True, kleur)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, y))
    pygame.display.flip()


def toon_game_over(scherm: pygame.Surface, groot_font, klein_font,
                   score: int, data_rijen: int):
    overlay = pygame.Surface((BREEDTE, HOOGTE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    scherm.blit(overlay, (0, 0))

    regels = [
        (groot_font, "GAME OVER",                          ROOD,        HOOGTE // 2 - 80),
        (klein_font, f"Score: {score}",                    TEKST_KLEUR, HOOGTE // 2 - 20),
        (klein_font, f"{data_rijen} frames opgeslagen",    GROEN,       HOOGTE // 2 + 10),
        (klein_font, f"Bestand: {CSV_BESTAND}",            BLAUW,       HOOGTE // 2 + 36),
        (klein_font, "R = opnieuw  |  Q = afsluiten",      GEEL,        HOOGTE // 2 + 80),
    ]
    for font, tekst, kleur, y in regels:
        opp = font.render(tekst, True, kleur)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, y))
    pygame.display.flip()


def toon_pauze(scherm: pygame.Surface, groot_font, klein_font):
    overlay = pygame.Surface((BREEDTE, HOOGTE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    scherm.blit(overlay, (0, 0))

    regels = [
        (groot_font, "PAUZE",                    GEEL,        HOOGTE // 2 - 80),
        (klein_font, "SPATIE = doorgaan",        TEKST_KLEUR, HOOGTE // 2 - 10),
        (klein_font, "R = opnieuw starten",      TEKST_KLEUR, HOOGTE // 2 + 16),
        (klein_font, "Q = afsluiten",            TEKST_KLEUR, HOOGTE // 2 + 42),
    ]
    for font, tekst, kleur, y in regels:
        opp = font.render(tekst, True, kleur)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, y))
    pygame.display.flip()


def toon_aftelling(scherm: pygame.Surface, groot_font, klok):
    for i in range(3, 0, -1):
        scherm.fill(ACHTERGROND)
        opp = groot_font.render(str(i), True, GEEL)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, HOOGTE // 2 - 20))
        pygame.display.flip()
        pygame.time.wait(1000)


# ── Spellogica ─────────────────────────────────────────────────────────────────

def nieuwe_steen(basis_snelheid: float) -> dict:
    breedte = random.randint(18, 40)
    hoogte  = random.randint(16, 30)
    x       = random.randint(0, BREEDTE - breedte)
    return {
        "rect":     pygame.Rect(x, -hoogte, breedte, hoogte),
        "snelheid": basis_snelheid + random.uniform(0, 1.5),
        "kleur":    random.choice(STEEN_KLEUREN),
    }


def speel_ronde() -> bool:
    """
    Speel één ronde. Geeft True terug als de speler opnieuw wil spelen,
    False als hij wil afsluiten.
    """
    pygame.init()
    scherm = pygame.display.set_mode((BREEDTE, HOOGTE))
    pygame.display.set_caption("Steen Ontwijker — trainingsdata recorder")
    klok = pygame.time.Clock()

    groot_font = pygame.font.SysFont("monospace", 30, bold=True)
    klein_font = pygame.font.SysFont("monospace", 15)

    schrijf_csv_header()

    # Wacht op startscherm
    toon_startscherm(scherm, groot_font, klein_font)
    wacht = True
    while wacht:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    wacht = False
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

    # ── Spelstaat ──
    speler = pygame.Rect(BREEDTE // 2 - 20, HOOGTE - 60, 40, 20)
    speler_snelheid = 5

    stenen: list[dict] = []
    spawn_timer    = 0
    spawn_interval = 60      # frames tussen nieuwe stenen
    basis_snelheid = 2.5

    score      = 0
    frame_nr   = 0
    data_rijen = 0           # teller voor dit rondje

    # ── Hoofdlus ──
    while True:
        klok.tick(FPS)
        frame_nr += 1
        score = frame_nr // FPS  # score in seconden overleefd

        # Moeilijkheidsgraad neemt toe
        spawn_interval = max(20, 60 - score // 3)
        basis_snelheid = 2.5 + score / 40

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit();
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:  # ← nieuw
                toon_pauze(scherm, groot_font, klein_font)
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit();
                            sys.exit()
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_q:
                                pygame.quit();
                                sys.exit()
                            if event.key == pygame.K_r:
                                return True
                            if event.key == pygame.K_SPACE:
                                #toon_aftelling(scherm, groot_font, klok)__________<(aftelling is optioneel na pauze)
                                break
                    else:
                        continue
                    break

        # Spelerinput
        toetsen = pygame.key.get_pressed()
        actie = 0
        if toetsen[pygame.K_LEFT]  or toetsen[pygame.K_a]:
            speler.x -= speler_snelheid
            actie = -1
        if toetsen[pygame.K_RIGHT] or toetsen[pygame.K_d]:
            speler.x += speler_snelheid
            actie = 1
        speler.x = max(0, min(BREEDTE - speler.width, speler.x))

        # Stenen spawnen
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            stenen.append(nieuwe_steen(basis_snelheid))
            spawn_timer = 0

        # Stenen bewegen en verwijderen
        for s in stenen:
            s["rect"].y += s["snelheid"]
        stenen = [s for s in stenen if s["rect"].top < HOOGTE + 40]

        # Botsingsdetectie
        geraakt = any(speler.colliderect(s["rect"]) for s in stenen)
        if geraakt:
            break

        # Data opslaan (elke 3 frames)
        if frame_nr % 3 == 0:
            rij = maak_rij(speler, stenen, score, actie)
            sla_rij_op(rij)
            data_rijen += 1

        # Tekenen
        scherm.fill(ACHTERGROND)
        #teken_raster(scherm)______________________________________________<Raster(optioneel)
        for s in stenen:
            teken_steen(scherm, s)
        teken_speler(scherm, speler)
        teken_hud(scherm, klein_font, score, data_rijen, len(stenen))
        pygame.display.flip()

    # ── Game-over scherm ──
    toon_game_over(scherm, groot_font, klein_font, score, data_rijen)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True   # opnieuw spelen
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()


# ── Startpunt ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    while speel_ronde():
        pass