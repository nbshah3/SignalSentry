from __future__ import annotations

import json
from pathlib import Path

from app.db.session import init_db, session_scope
from app.seed import seed_sample_data


def main() -> None:
    force = True
    init_db()
    with session_scope() as session:
        result = seed_sample_data(session, force=force)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
