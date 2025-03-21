# Aktualisierter Plan zur Installation und Ausführung des Orpheus TTS Projekts mit uv

## Übersicht

Dieser Plan beschreibt die Schritte, die notwendig sind, um das Orpheus TTS Projekt mit `uv` installierbar und ausführbar zu machen, einschließlich eines OpenAI-kompatiblen API-Endpunkts.

## Schritte

1.  **Erstellen der `pyproject.toml`-Datei:** (Unverändert)

    Eine `pyproject.toml`-Datei wird im Hauptverzeichnis des Projekts erstellt. Diese Datei enthält die folgenden Informationen:

    *   **Projektdetails:**
        *   Name: orpheus-tts
        *   Version: 0.1.0
        *   Beschreibung: Ein Text-to-Speech-Projekt mit Orpheus.
        *   Autoren: grait.io Mariusz Kreft, 1@grait.io
        *   Lizenz: Apache License 2.0
    *   **Abhängigkeiten:**
        ```
        [project.dependencies]
        torch = ">=2.0.0"
        numpy = ">=1.20.0"
        sounddevice = ">=0.4.4"
        requests = ">=2.25.0"
        wave = ">=0.0.2"
        snac = ">=1.2.1"
        fastapi = ">=0.104.0" # Hinzugefügt für die API
        uvicorn = {extras = ["standard"], version = ">=0.12.0"} # Hinzugefügt für den API-Server
        ```
    *   **Einstiegspunkt:**
        ```
        [project.scripts]
        orpheus-tts = "gguf_orpheus:main"
        ```
        Dies konfiguriert `gguf_orpheus.py` als Einstiegspunkt. Die Funktion `main` in `gguf_orpheus.py` wird ausgeführt, wenn der Benutzer `uv run orpheus-tts` ausführt.

2.  **Überprüfen und Anpassen von `gguf_orpheus.py`:**

    *   Die Datei `gguf_orpheus.py` wird überprüft, um sicherzustellen, dass die Befehlszeilenargumente (`--text`, `--voice`, `--output`, `--temperature`, `--top_p`,`--repetition_penalty`, `--list-voices`) korrekt mit `argparse` geparst werden.
    *   Eine `main`-Funktion wird hinzugefügt, die diese Argumente entgegennimmt.
    *   Implementieren Sie die Logik für `--list-voices`.

3.  **Neues Modul für OpenAI-kompatiblen Endpunkt erstellen (`openai_api.py`):**

    Ein neues Modul, `openai_api.py`, wird erstellt, das einen FastAPI-Endpunkt bereitstellt.

    *   **Endpunkte:**
        *   `/v1/audio/speech`: Dieser Endpunkt akzeptiert Text und gibt eine WAV-Datei mit der generierten Sprache zurück (kompatibel mit dem OpenAI API-Format).
            *   Anfrageparameter: `text` (erforderlich), `voice` (optional, Standardwert "tara"), `temperature` (optional), `top_p` (optional), `repetition_penalty` (optional).
        *   `/v1/voices`: Dieser Endpunkt gibt eine Liste der verfügbaren Stimmen zurück.
        *   `/v1/capabilities`: Dieser Endpunkt gibt eine Beschreibung der verfügbaren Funktionen und Optionen des Programms zurück.

    *   Dieses Modul verwendet die Funktionen aus `gguf_orpheus.py`, um die Sprachsynthese durchzuführen.
    *   FastAPI wird verwendet, um die API zu erstellen.

4.  **Integration:**

    Stellen Sie sicher, dass `openai_api.py` die Funktionen aus `gguf_orpheus.py` korrekt aufruft.

5.  **Testen der Installation und Ausführung:**

    *   Installation mit `uv pip install .`.
    *   Testen des ursprünglichen Einstiegspunkts: `uv run orpheus-tts --text "Hallo Welt" --voice tara --output output.wav`.
    *   Starten des FastAPI-Servers: `uvicorn openai_api:app --reload`.
    *   Testen des OpenAI-kompatiblen Endpunkts: Senden einer POST-Anfrage an `/v1/audio/speech` mit den entsprechenden Parametern.
    *   Testen des `/v1/voices`-Endpunkts.
    *   Testen des `/v1/capabilities`-Endpunkts.

## Anmerkungen

```mermaid
graph TD
    subgraph CLI
        A[Benutzer gibt Befehl ein: uv run orpheus-tts ...] --> B(pyproject.toml leitet an gguf_orpheus.py:main weiter);
        B --> C{gguf_orpheus.py:main};
        C --> D[Verarbeitet Befehlszeilenargumente];
        D --> E[Generiert Sprache];
        E --> F[Speichert Audiodatei];
    end
    subgraph API
        G[Benutzer sendet Anfrage an /v1/audio/speech] --> H(openai_api.py);
        H --> I{FastAPI};
        I --> J[Ruft gguf_orpheus.py Funktionen auf];
        J --> K[Generiert Sprache];
        K --> L[Gibt WAV-Datei zurück];
    end
        M[Benutzer sendet Anfrage an /v1/voices] --> N(openai_api.py);
        N --> O{FastAPI}
        O --> P[return list of voices]
        Q[Benutzer sendet Anfrage an /v1/capabilities] --> R(openai_api.py);
        R --> S{FastAPI}
        S --> T[return capabilities]
