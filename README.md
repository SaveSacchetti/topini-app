# Topini's App

Un'app desktop in Python per comunicare con Topino tramite gesti delle mani.

## Funzionalità
- Pagina iniziale con titolo e call-to-action.
- Accesso alla webcam e riproduzione video.
- Rilevamento mano e landmark con MediaPipe.
- Riconoscimento gesti: cuore con due mani, saluto (wave) con una o due mani.
- Messaggi a schermo: "Anche topino ti ama tanto!" e "Anche topino ti saluta!".

## Architettura a pagine / moduli
- `src/main.py`: bootstrap dell'app.
- `src/ui/`: interfaccia grafica (Qt)
  - `home_page.py`: pagina iniziale.
  - `gesture_page.py`: pagina funzionale con video e overlay.
  - `theme.py`: colori e stile.
- `src/core/`: logica di dominio
  - `video_capture.py`: cattura video con OpenCV in thread separato.
  - `hand_tracker.py`: tracking mani con MediaPipe.
  - `gesture_detector.py`: logica per i gesti (cuore, saluto).
- `src/utils/`: utilità
  - `types.py`: tipi condivisi.

Questa suddivisione rende semplice estendere con nuove pagine o gesti.

## Requisiti
- Python 3.9+
- Windows, macOS o Linux con webcam.

## Setup
1. Creare un virtualenv e installare le dipendenze:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Avvio:

```cmd
.venv\Scripts\activate
python -m src.main
```

## Troubleshooting
- Webcam occupata: chiudere altre app che usano la camera.
- Permessi camera su macOS: autorizzare il Terminale/VS Code nelle Preferenze.
- Se il video è lento, ridurre la risoluzione in `video_capture.py`.