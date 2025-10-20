# 🌍 OurPlaneteAnalyzing – API dla analizy stanu planety Ziemia

Model OurPlaneteAnalyzing oparty na GPT analizuje dane dotyczące klimatu, środowiska i geofizyki.
Integruje dane z NASA, ESA, WMO i IPCC, generując raporty w formatach PDF lub JSON.

## Endpointy API
- `/analyze` – analiza danych i odpowiedź GPT
- `/generate-report` – generowanie raportu PDF
- `/status` – sprawdzenie stanu modelu

## Instalacja
```bash
pip install pyyaml json5
python generate_openapi_files.py
```

## Licencja
MIT License