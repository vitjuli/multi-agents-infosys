#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_centre_site_selector.data_paths import CANDIDATE_FEATURES_CSV, ensure_dirs
from data_centre_site_selector.preprocess import build_candidate_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cached candidate-region feature table.")
    parser.add_argument("--include-flood", action="store_true", help="Attempt to process the large EA flood-zone ZIP.")
    args = parser.parse_args()
    ensure_dirs()
    features, diagnostics = build_candidate_features(include_flood=args.include_flood)
    features.to_csv(CANDIDATE_FEATURES_CSV, index=False)
    print(f"Wrote {CANDIDATE_FEATURES_CSV} with {len(features)} rows.")
    print("Diagnostics:")
    for item in diagnostics:
        print(f"- {item}")


if __name__ == "__main__":
    main()
