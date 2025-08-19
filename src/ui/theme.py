"""
Centralized color rAPP_TITLE = "Topini's App"
APP_LOGO = "🐭💕🐭"  # Due topini con cuore rosso (più compatibile)
APP_TAGLINE = "L'app che non fa sentire mai sola la mia Topina"
CTA_TEXT = "Avvia la comunicazione a gesti con Topino" for the UI theme.
"""

from __future__ import annotations

import string

# Core text colors
TEXT = "#FFFFFF"
MUTED = "#B0B3C0"

# Roles
PRIMARY = "#8B5CF6"           # vivid violet
SECONDARY = "#38BDF8"         # bright sky blue
SURFACE = "#15182A"           # elevated surfaces
SURFACE_VARIANT = "#0F1426"   # subtle alternate surface
OUTLINE = "#2A2F45"           # borders/lines on dark
SUCCESS = "#22C55E"           # green
ERROR = "#EF4444"             # red

# App background (refined dark)
BG = "#121426"

APP_TITLE = "Topini's App"
APP_LOGO = "🐭💕🐭"  # Due topini con simbolo di amicizia/coppia al centro
APP_TAGLINE = "L'app che non fa sentire mai sola la mia Topina"
CTA_TEXT = "Avvia la comunicazione a gesti con Topino"

_STYLE_TEMPLATE = r"""
QWidget {
    background-color: $BG;
    color: $TEXT;
    font-family: 'Segoe UI Variable', 'Inter', 'Segoe UI', Arial, sans-serif;
    font-size: 15px; /* body base 14–16 */
    font-weight: 400;
}
/* Backdrop area behind the video card (subtle radial glow) */
QWidget#videoArea {
    background-color: qradialgradient(cx:0.5, cy:0.45, radius:0.85,
                                      fx:0.5, fy:0.45,
                                      stop:0 rgba(255,255,255,12),
                                      stop:0.35 rgba(255,255,255,6),
                                      stop:1 rgba(0,0,0,0));
}
QPushButton {
    background-color: $PRIMARY;
    color: $TEXT;
    /* reserve space for focus ring without layout shift */
    border: 2px solid transparent;
    border-radius: 12px; /* 12 per pulsanti */
    padding: 16px 32px;   /* Aumentato +30%: da 12px 24px */
    font-size: 24px;      /* Aumentato +30%: da 18px */
    font-weight: 600;
}
QPushButton:hover {
    background-color: #7C3AED; /* slightly lighter */
}
QPushButton:pressed {
    background-color: #6D28D9; /* darker on press */
}
/* prominent focus ring for accessibility */
QPushButton:focus {
    outline: none;
    border: 2px solid rgba(56, 189, 248, 0.9); /* SECONDARY */
}
QLabel#logo {
    font-size: 80px;     /* Grande per l'emoji logo */
    margin-bottom: 20px; /* Spazio sotto il logo */
    text-align: center;
}
QLabel#title {
    font-size: 55px;     /* Aumentato +30%: da 42px */
    font-weight: 900;    /* Massimo grassetto possibile (da 800) */
    color: $TEXT;
    padding-bottom: 6px; /* Aumentato +30%: da 4px */
    letter-spacing: 0.5px; /* Aumentato +30%: da 0.4px */
}
QLabel#subtitle {
    font-size: 29px;     /* Aumentato +30%: da 22px */
    font-weight: 600;
    font-style: italic;  /* Aggiunto corsivo */
    color: $MUTED;
    letter-spacing: 0.4px; /* Aumentato +30%: da 0.3px */
}
/* Old overlay label kept for compatibility */
QLabel#overlay {
    background-color: rgba(0,0,0,180);
    border: 1px solid rgba(255,255,255,60);
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 20px;
    font-weight: 600;
    color: $TEXT;
}

/* Banner now positioned in topbar - full width available */
QWidget#overlayBanner {
    /* Sfondo molto più chiaro per distinguersi chiaramente dal resto */
    background: rgba(80, 90, 120, 255); /* Molto più chiaro - grigio azzurrino */
    border: 1px solid rgba(255, 255, 255, 120); /* Bordo ancora più visibile */
    border-radius: 16px; /* pill radius 14–16 */
    /* Rimosso max-width per estendersi fino alla fine */
}
/* Keep variants as subtle but distinguishable backgrounds */
/* Per-kind banner gradient variants con sfondo molto più chiaro */
QWidget#overlayBanner[kind="wave"] {
    background: rgba(80, 90, 120, 255); /* Stesso sfondo molto più chiaro per consistenza */
}
QWidget#overlayBanner[kind="heart"] {
    background: rgba(80, 90, 120, 255); /* Stesso sfondo molto più chiaro per consistenza */
}
/* Accent stripe at left side of the banner - estesa fino in fondo */
QWidget#overlayAccent {
    background: rgba(255,255,255,0.18); /* default subtle fallback */
    border-top-left-radius: 16px;
    border-bottom-left-radius: 16px;
}
QWidget#overlayAccent[kind="wave"] {
    background: rgba(56, 189, 248, 0.95); /* sky */
}
QWidget#overlayAccent[kind="heart"] {
    background: rgba(239, 68, 68, 0.95); /* red */
}
QWidget#overlayAccent[kind="middle_finger"] {
    background: rgba(251, 191, 36, 0.95); /* yellow/amber */
}
QLabel#overlayText {
    color: $TEXT;
    font-size: 20px;
    font-weight: 700;
}
/* New chip + typographic hierarchy inside the banner */
QLabel#overlayTitle {
    color: $TEXT;
    font-size: 21px; /* 20–22px */
    font-weight: 800; /* bold */
    letter-spacing: 0.2px;
}
QLabel#overlaySubtitle {
    color: $MUTED;  /* muted */
    font-size: 13.5px; /* 13–14px */
    font-weight: 600;
}
QLabel#overlayIcon {
    min-width: 30px; min-height: 30px;
    max-width: 30px; max-height: 30px;
    border-radius: 15px; /* circle */
    color: white; /* emoji/text color when applicable */
    font-size: 18px; /* slight scale */
    background-color: rgba(255,255,255,0.12); /* default subtle */
}
/* Per-kind chip background tints */
QLabel#overlayIcon[kind="heart"] {
    background-color: rgba(239, 68, 68, 0.85); /* ERROR red */
}
QLabel#overlayIcon[kind="wave"] {
    background-color: rgba(56, 189, 248, 0.85); /* SECONDARY sky */
}
QProgressBar#overlayProgress {
    /* Integrated time bar: hide track and remove borders */
    background: transparent;
    border: none;
    margin: 0px; /* Rimuovi margini laterali per riempire tutto lo spazio */
}
QProgressBar#overlayProgress::chunk {
    background-color: rgba(255,255,255,220); /* more visible */
    border: none;
    border-radius: 0px; /* remove rounded ends to fill completely */
    margin: 0px; /* ensures chunk fills the available space */
    padding: 0px; /* ensures no internal padding */
}
/* Per-kind accent for time bar (slight tint shift if wanted) */
QProgressBar#overlayProgress[kind="wave"]::chunk {
    background-color: rgba(56, 189, 248, 230); /* sky */
}
QProgressBar#overlayProgress[kind="heart"]::chunk {
    background-color: rgba(239, 68, 68, 230); /* red */
}
QProgressBar#overlayProgress[kind="middle_finger"]::chunk {
    background-color: rgba(251, 191, 36, 230); /* yellow/amber */
}
"""

STYLE_SHEET = string.Template(_STYLE_TEMPLATE).substitute(
    BG=BG,
    TEXT=TEXT,
    MUTED=MUTED,
    PRIMARY=PRIMARY,
)
