# OurPlanetAnalyzing

OurPlanetAnalyzing to API demonstracyjne do analizy danych klimatycznych,
srodowiskowych i geofizycznych. Projekt udostepnia endpointy do zadawania
pytan analitycznych, generowania raportu oraz sprawdzania statusu uslugi.

## Uruchomienie

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Po uruchomieniu API jest dostepne pod adresem `http://127.0.0.1:8000`.
Dokumentacja OpenAPI jest dostepna pod `http://127.0.0.1:8000/docs`.

## Endpointy

- `POST /analyze` - zwraca przykladowa analize dla przekazanego pytania.
- `POST /generate-report` - zwraca metadane wygenerowanego raportu.
- `GET /status` - sprawdza stan aplikacji.

## Generowanie OpenAPI

```bash
python generate_openapi_files.py
```

Polecenie odswieza pliki `ourplaneteanalyzing_full_openapi.json` i
`ourplaneteanalyzing_full_openapi.yaml` na podstawie dzialajacej aplikacji.
