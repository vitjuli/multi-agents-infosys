"""Ground-truth validation against known UK data centre clusters.

Sources: Datacenter Map, CBRE/JLL DC market reports, UK government planning data.
These LADs are documented locations of major commercial data centre infrastructure.
"""
from __future__ import annotations

# Known UK data centre LAD clusters — publicly documented locations
KNOWN_DC_CLUSTERS: dict[str, list[str]] = {
    "London Core (Docklands/City)": [
        "Tower Hamlets", "City of London", "Hackney", "Southwark", "Newham",
    ],
    "London West / M4 Corridor": [
        "Slough", "Hounslow", "Hillingdon", "Ealing", "Windsor and Maidenhead",
    ],
    "Thames Valley": [
        "Reading", "Wokingham", "South Oxfordshire", "Bracknell Forest",
    ],
    "Manchester / North West": [
        "Manchester", "Salford", "Trafford", "Stockport",
    ],
    "Scotland Central Belt": [
        "City of Edinburgh", "Glasgow City", "North Lanarkshire", "Midlothian",
    ],
    "West Midlands": [
        "Birmingham", "Solihull", "Coventry",
    ],
    "Yorkshire": [
        "Leeds", "Wakefield", "Bradford",
    ],
}

ALL_KNOWN_DC_LADS: list[str] = [
    lad for cluster in KNOWN_DC_CLUSTERS.values() for lad in cluster
]


def _name_match(rec_name: str, known_name: str) -> bool:
    """Fuzzy match — substring in either direction, case-insensitive."""
    r, k = rec_name.lower(), known_name.lower()
    return k in r or r in k


def compute_precision_at_k(
    ranked_regions: list[str],
    k: int = 20,
) -> dict:
    """Return precision@K: fraction of top-K recommendations matching known DC LADs."""
    top_k = ranked_regions[:k]
    hits = [
        r for r in top_k
        if any(_name_match(r, known) for known in ALL_KNOWN_DC_LADS)
    ]
    precision = len(hits) / k if k > 0 else 0.0
    return {
        "precision_at_k": round(precision, 3),
        "k": k,
        "hits": hits,
        "hit_count": len(hits),
        "total_known_lads": len(ALL_KNOWN_DC_LADS),
        "pass": precision >= 0.10,   # at least 10% of top-20 are known DC clusters
    }


def check_known_sites_ranked(
    ranked_regions: list[str],
    top_n: int = 50,
) -> dict:
    """Check how many known DC LADs appear in the top-N ranked candidates."""
    top_n_set = set(ranked_regions[:top_n])
    found: dict[str, list[str]] = {}
    missing: list[str] = []
    for cluster, lads in KNOWN_DC_CLUSTERS.items():
        cluster_hits = [
            lad for lad in lads
            if any(_name_match(r, lad) for r in top_n_set)
        ]
        if cluster_hits:
            found[cluster] = cluster_hits
        else:
            missing.append(cluster)
    coverage = len(found) / len(KNOWN_DC_CLUSTERS)
    return {
        "clusters_found": found,
        "clusters_missing": missing,
        "cluster_coverage": round(coverage, 3),
        "total_clusters": len(KNOWN_DC_CLUSTERS),
        "pass": coverage >= 0.50,   # at least half of known clusters represented
    }
