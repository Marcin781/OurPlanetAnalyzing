import yaml, json

corrected_openapi_yaml = """openapi: 3.0.0
info:
  title: OurPlaneteAnalyzing API
  version: 1.0.0
  description: API do analizy klimatu i danych ekologicznych
servers:
  - url: https://api.twojadomena.pl/v1
paths:
  /analyze:
    post:
      summary: Zadanie pytania modelowi GPT
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                question:
                  type: string
                  example: Sprawdz emisje CO2 w Europie
      responses:
        '200':
          description: Odpowiedz modelu
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
                    example: Emisje CO2 w Europie wyniosly 3.1 Gt w 2024 roku
"""

with open("ourplaneteanalyzing_full_openapi.yaml", "w") as f:
    f.write(corrected_openapi_yaml.strip())

yaml_data = yaml.safe_load(corrected_openapi_yaml)
with open("ourplaneteanalyzing_full_openapi.json", "w") as f:
    json.dump(yaml_data, f, indent=2)