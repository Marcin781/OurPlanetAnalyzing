# Dziennik Planety — Data Quality Policy

## 1. Zasada źródła pierwotnego

Każdy moduł powinien preferować oficjalnego dostawcę danych. Pośrednie serwisy mogą być używane tylko jako fallback i muszą być oznaczone w metadanych.

## 2. Wymagane metadane rekordu

Każda obserwacja powinna mieć co najmniej:

- `source`
- `dataset`
- `metric`
- `value`
- `unit`
- `observed_at`
- `retrieved_at`
- `status` (`final`, `preliminary`, `revised`, `missing`, `error`)
- `quality_flag`
- `source_version` lub DOI, jeśli dostawca go udostępnia

## 3. Revision-aware storage

Korekta danych nie może być traktowana jako nowy pomiar. Rekord identyfikujemy logicznie przez `source + dataset + metric + observed_at + spatial_key` i przechowujemy wersję oraz czas pobrania. Najnowsza wersja jest używana w dashboardzie, a poprzednia pozostaje w historii audytowej.

## 4. Baselines

Nie wolno łączyć anomalii z różnymi okresami bazowymi bez jawnego przeliczenia. Dashboard musi pokazywać bazę obok każdej anomalii.

Przykład: NASA GISTEMP używa w swoich mapach miesięcznych norm 1951–1980. Copernicus/ERA5 ma własne definicje i okresy referencyjne. Są prezentowane jako osobne serie.

## 5. Dane wstępne

Dane oznaczone przez dostawcę jako preliminary pozostają preliminary. Aplikacja nie może przedstawiać ich jako ostatecznych.

NOAA GML wskazuje, że najnowszy rok danych CO2 może podlegać kalibracji i kontroli jakości; globalna średnia i Mauna Loa są też różnymi produktami i nie mogą być bezpośrednio utożsamiane.

## 6. Walidacja

Przed zapisem należy sprawdzić:

1. poprawność typu i jednostki,
2. zakres fizycznie możliwy dla danej metryki,
3. kompletność wymaganych pól,
4. świeżość danych,
5. status dostawcy,
6. zmianę schematu odpowiedzi API.

Błąd pojedynczego źródła nie może zatrzymać całego collectora. Moduł otrzymuje status `error`, a pozostałe źródła są nadal przetwarzane.

## 7. Anomalie i trendy

Anomalia jest zawsze liczona względem jawnie określonego baseline. Trend jest wyliczany z szeregu czasowego po walidacji i nie jest przedstawiany jako przyczynowość.

## 8. Audit trail

Każdy snapshot powinien mieć:

- timestamp pobrania,
- listę źródeł,
- status każdego źródła,
- liczbę rekordów,
- błędy/warnings,
- wersję collectora.

To pozwala odtworzyć, skąd pochodzi każda wartość pokazana użytkownikowi.
