import json
from pathlib import Path

import yaml

from app import app


ROOT = Path(__file__).resolve().parent


def main() -> None:
    schema = app.openapi()

    (ROOT / "ourplaneteanalyzing_full_openapi.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / "ourplaneteanalyzing_full_openapi.yaml").write_text(
        yaml.safe_dump(schema, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
