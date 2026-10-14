"""Command-line tasks. Run from backend/:

    python -m app.cli create-admin     # reads NUTRIPLAN_ADMIN_EMAIL / _PASSWORD / _NAME
    python -m app.cli seed-catalogue   # loads the illustrative food & recipe dataset

Credentials are read from environment variables only – never from arguments or files in Git.
"""

import argparse
import os
import sys

from pydantic import ValidationError

from app.db.session import get_session_factory
from app.services.auth_service import create_or_promote_admin
from app.services.seed_service import seed_catalogue


def create_admin() -> int:
    email = os.environ.get("NUTRIPLAN_ADMIN_EMAIL", "").strip()
    password = os.environ.get("NUTRIPLAN_ADMIN_PASSWORD", "")
    name = os.environ.get("NUTRIPLAN_ADMIN_NAME", "NutriPlan Administrator").strip()
    if not email or not password:
        print(
            "Set NUTRIPLAN_ADMIN_EMAIL and NUTRIPLAN_ADMIN_PASSWORD in the environment first.",
            file=sys.stderr,
        )
        return 2
    try:
        with get_session_factory()() as db:
            result = create_or_promote_admin(db, email=email, full_name=name, password=password)
    except ValidationError as exc:
        messages = "; ".join(str(e["msg"]).removeprefix("Value error, ") for e in exc.errors())
        print(f"Invalid admin details: {messages}", file=sys.stderr)
        return 2
    print(f"Administrator {email} {result}.")
    return 0


def seed() -> int:
    with get_session_factory()() as db:
        counts = seed_catalogue(db)
    if counts["foods"] == 0:
        print("Catalogue already contains foods – nothing seeded.")
    else:
        print(
            f"Seeded {counts['foods']} foods and {counts['recipes']} recipes "
            "(illustrative development data)."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="NutriPlan tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("create-admin", help="Create or promote the administrator from env vars")
    sub.add_parser("seed-catalogue", help="Load the illustrative food and recipe dataset")
    args = parser.parse_args(argv)
    return create_admin() if args.command == "create-admin" else seed()


if __name__ == "__main__":
    raise SystemExit(main())
