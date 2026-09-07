from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from korea_business_lifecycle.kaggle_dataset_maintenance import (  # noqa: E402
    APPROVED_PUBLIC_VERSION_NUMBER,
    KaggleDatasetMaintenanceError,
    apply_metadata_update_plan,
    build_metadata_update_plan,
    get_live_metadata_coverage,
    get_usability_rating,
    load_live_context,
    summarize_plan,
)


def _kaggle_session():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise KaggleDatasetMaintenanceError(
            "the Kaggle CLI package is required to authenticate this maintenance command"
        ) from exc

    api = KaggleApi()
    api.authenticate()
    client = api.build_kaggle_client()
    http_client = client.http_client()
    http_client._init_session()
    session = http_client._session
    if session is None:
        raise KaggleDatasetMaintenanceError("Kaggle CLI did not initialize an authenticated session")
    return session


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize the approved file and column descriptions into Kaggle's Data Explorer metadata backend. "
            "The default is a read-only dry run; pass --apply to write metadata."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the validated metadata plan to the current approved Kaggle dataset version",
    )
    parser.add_argument(
        "--version",
        type=int,
        default=APPROVED_PUBLIC_VERSION_NUMBER,
        help=(
            "dataset version number to maintain; defaults to the repository-approved public version "
            f"({APPROVED_PUBLIC_VERSION_NUMBER})"
        ),
    )
    args = parser.parse_args()

    try:
        public_session = requests.Session()
        public_context = load_live_context(
            public_session,
            dataset_version_number=args.version,
        )
        session = _kaggle_session()
        authenticated_context = load_live_context(
            session,
            dataset_version_number=public_context.version_number,
        )
        if (
            authenticated_context.dataset_version_id != public_context.dataset_version_id
            or authenticated_context.databundle_version_id != public_context.databundle_version_id
        ):
            raise KaggleDatasetMaintenanceError(
                "authenticated Kaggle view disagrees with the current public dataset version"
            )
        context, updates = build_metadata_update_plan(session, authenticated_context)
        coverage = get_live_metadata_coverage(public_session, public_context)
        before = get_usability_rating(public_session)
        output: dict[str, object] = {
            "mode": "apply" if args.apply else "dry-run",
            "plan": summarize_plan(context, updates),
            "version_2_metadata_coverage": coverage,
            "legacy_dataset_id_only_usability": before,
            "usability_scope_warning": (
                "GetDatasetUsabilityRating cannot pin a dataset version and is known to return a stale implicit-version "
                "rating for this dataset. Use the explicit Version 2 web UI or authenticated Version 2 SDK response "
                "for the current usability score."
            ),
        }
        if args.apply:
            responses = apply_metadata_update_plan(session, updates)
            output["update_calls"] = len(responses)
            output["legacy_dataset_id_only_usability_after"] = get_usability_rating(public_session)
        print(json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except KaggleDatasetMaintenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
