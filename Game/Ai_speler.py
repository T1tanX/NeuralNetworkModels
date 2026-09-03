import pygame
import random
import pickle
import numpy as np
import sys
import os
import tensorflow as tf
from tensorflow import keras

# ── Instellingen ──────────────────────────────────────────────────────────────
BREEDTE, HOOGTE  = 400, 600
FPS              = 60
MODEL_BESTAND    = "model_keras.keras"
SCALER_BESTAND   = "scaler.pkl"

# Kleuren
ACHTERGROND  = (10,  10,  26)
SPELER_KLEUR = (93, 202, 165)   # groen — zodat je ziet dat het de AI is
SPELER_RAND  = (159, 225, 205)
TEKST_KLEUR  = (255, 255, 255)
ROOD         = (226,  75,  74)
GEEL         = (239, 159,  39)
BLAUW        = (133, 183, 235)
GROEN        = ( 93, 202, 165)
GRIJS        = ( 80,  80,  80)
PAARS        = (127, 119, 221)

STEEN_KLEUREN = [ROOD, GEEL, BLAUW, PAARS]

# ── Model laden ───────────────────────────────────────────────────────────────

def laad_model():
    if not os.path.exists(MODEL_BESTAND):
        print(f"❌ '{MODEL_BESTAND}' niet gevonden. Voer eerst train_model.ipynb uit!")
        sys.exit()
    if not os.path.exists(SCALER_BESTAND):
        print(f"❌ '{SCALER_BESTAND}' niet gevonden. Voer eerst train_model.ipynb uit!")
        sys.exit()
    model  = keras.models.load_model(MODEL_BESTAND)
    with open(SCALER_BESTAND, "rb") as f:
        scaler = pickle.load(f)
    print("✅ Model geladen.")
    return model, scaler


def voorspel_actie(model, scaler, speler: pygame.Rect,
                   stenen: list, score: int) -> int:
    """
    Laat het neurale netwerk beslissen.
    Keras-klassen: 0 = links, 1 = stil, 2 = rechts
    Teruggegeven actie: -1 / 0 / 1 (zoals in de game)
    """
    dichtste     = dichtstbijzijnde_steen(speler, stenen)
    steen_x      = dichtste["rect"].centerx  if dichtste else BREEDTE // 2
    steen_y      = dichtste["rect"].centery  if dichtste else -100
    steen_snelh  = dichtste["snelheid"]      if dichtste else 0.0
    rel_verschil = steen_x - speler.centerx

    features = np.array([[
        speler.centerx,
        speler.left,
        BREEDTE - speler.right,
        steen_x,
        steen_y,
        steen_snelh,
        rel_verschil,
        len(stenen),
        score,
    ]], dtype=np.float32)

    features_scaled = scaler.transform(features).astype(np.float32)
    probs  = model(features_scaled, training=False).numpy()[0]  # veel sneller dan model.predict()
    klasse = int(np.argmax(probs))                              # 0, 1 of 2
    return klasse - 1                                           # terug naar -1, 0, 1


# ── Helperfuncties ─────────────────────────────────────────────────────────────

def dichtstbijzijnde_steen(speler: pygame.Rect, stenen: list):
    if not stenen:
        return None
    return min(stenen, key=lambda s: abs(s["rect"].centerx - speler.centerx)
                                   + abs(s["rect"].centery - speler.centery))


def nieuwe_steen(basis_snelheid: float) -> dict:
    breedte = random.randint(18, 40)
    hoogte  = random.randint(16, 30)
    x       = random.randint(0, BREEDTE - breedte)
    return {
        "rect":     pygame.Rect(x, -hoogte, breedte, hoogte),
        "snelheid": basis_snelheid + random.uniform(0, 1.5),
        "kleur":    random.choice(STEEN_KLEUREN),
    }


# ── Tekenfuncties ──────────────────────────────────────────────────────────────

def teken_raster(scherm):
    for x in range(0, BREEDTE, 40):
        pygame.draw.line(scherm, (30, 30, 50), (x, 0), (x, HOOGTE))
    for y in range(0, HOOGTE, 40):
        pygame.draw.line(scherm, (30, 30, 50), (0, y), (BREEDTE, y))


def teken_speler(scherm, rect: pygame.Rect, actie: int, font):
    pygame.draw.rect(scherm, SPELER_KLEUR, rect, border_radius=5)
    antenne_x = rect.centerx - 3
    pygame.draw.rect(scherm, SPELER_RAND, (antenne_x, rect.top - 8, 6, 8))

    label = {-1: "", 0: "", 1: ""}[actie]
    opp = font.render(label, True, SPELER_RAND)
    scherm.blit(opp, (rect.x - 10, rect.top - 22))


def teken_steen(scherm, steen: dict):
    pygame.draw.rect(scherm, steen["kleur"], steen["rect"], border_radius=4)


def teken_hud(scherm, font, score: int, stenen: int, record: int):
    for tekst, pos in [
        (f"Score:  {score}",  (10, 10)),
        (f"Stenen: {stenen}", (10, 30)),
        (f"Record: {record}", (10, 50)),
    ]:
        scherm.blit(font.render(tekst, True, TEKST_KLEUR), pos)

    ai_label = font.render("AI SPEELT", True, GROEN)
    scherm.blit(ai_label, (BREEDTE - ai_label.get_width() - 10, 10))


def toon_startscherm(scherm, groot_font, klein_font):
    scherm.fill(ACHTERGROND)
    for font, tekst, kleur, y in [
        (groot_font, "AI SPELER",                           GROEN,       HOOGTE // 2 - 90),
        (klein_font, "Het getrainde netwerk speelt de game", TEKST_KLEUR, HOOGTE // 2 - 30),
        (klein_font, "Speler is GROEN (vs paars bij jou)",  GRIJS,       HOOGTE // 2 +  4),
        (klein_font, "Druk op SPATIEBALK om te starten",    GEEL,        HOOGTE // 2 + 60),
        (klein_font, "Q = afsluiten",                       GRIJS,       HOOGTE // 2 + 86),
    ]:
        opp = font.render(tekst, True, kleur)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, y))
    pygame.display.flip()


def toon_game_over(scherm, groot_font, klein_font, score: int, record: int):
    overlay = pygame.Surface((BREEDTE, HOOGTE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    scherm.blit(overlay, (0, 0))
    for font, tekst, kleur, y in [
        (groot_font, "GAME OVER",                      ROOD,        HOOGTE // 2 - 80),
        (klein_font, f"Score:  {score}",               TEKST_KLEUR, HOOGTE // 2 - 20),
        (klein_font, f"Record: {record}",              GROEN,       HOOGTE // 2 +  6),
        (klein_font, "R = opnieuw  |  Q = afsluiten",  GEEL,        HOOGTE // 2 + 60),
    ]:
        opp = font.render(tekst, True, kleur)
        scherm.blit(opp, (BREEDTE // 2 - opp.get_width() // 2, y))
    pygame.display.flip()


# ── Spelronde ──────────────────────────────────────────────────────────────────

def speel_ronde(model, scaler, record: int) -> tuple[bool, int]:
    pygame.init()
    scherm     = pygame.display.set_mode((BREEDTE, HOOGTE))
    pygame.display.set_caption("Steen Ontwijker — AI speler")
    klok       = pygame.time.Clock()
    groot_font = pygame.font.SysFont("monospace", 30, bold=True)
    klein_font = pygame.font.SysFont("monospace", 14)

    toon_startscherm(scherm, groot_font, klein_font)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    break
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
        else:
            continue
        break

    speler         = pygame.Rect(BREEDTE // 2 - 20, HOOGTE - 60, 40, 20)
    speler_snelh   = 5
    stenen: list   = []
    spawn_timer    = 0
    spawn_interval = 60
    basis_snelheid = 2.5
    score          = 0
    frame_nr       = 0
    laatste_actie  = 0

    while True:
        klok.tick(FPS)
        frame_nr      += 1
        score          = frame_nr // FPS
        spawn_interval = max(20, 60 - score // 3)
        basis_snelheid = 2.5 + score / 40

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.quit(); sys.exit()

        # AI beslist
        actie         = voorspel_actie(model, scaler, speler, stenen, score)
        laatste_actie = actie

        speler.x += actie * speler_snelh
        speler.x  = max(0, min(BREEDTE - speler.width, speler.x))

        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            stenen.append(nieuwe_steen(basis_snelheid))
            spawn_timer = 0

        for s in stenen:
            s["rect"].y += s["snelheid"]
        stenen = [s for s in stenen if s["rect"].top < HOOGTE + 40]

        if any(speler.colliderect(s["rect"]) for s in stenen):
            break

        scherm.fill(ACHTERGROND)
        #teken_raster(scherm)______________________________________________<Raster(optioneel)
        for s in stenen:
            teken_steen(scherm, s)
        teken_speler(scherm, speler, laatste_actie, klein_font)
        teken_hud(scherm, klein_font, score, len(stenen), record)
        pygame.display.flip()

    nieuw_record = max(record, score)
    toon_game_over(scherm, groot_font, klein_font, score, nieuw_record)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True, nieuw_record
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()


# ── Startpunt ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model, scaler = laad_model()
    record        = 0
    opnieuw       = True
    while opnieuw:
        opnieuw, record = speel_ronde(model, scaler, record)