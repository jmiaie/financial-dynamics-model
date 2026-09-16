# Data layout (Directive #9)

| Path | Tracked? | Purpose |
|---|---|---|
| `data/raw/` | **No** (gitignored) | Frozen Yahoo/FRED/SEC snapshots. Never commit. |
| `data/manifests/` | **Yes** | Provenance manifests + checksums after freeze. |

Acquire with `scripts/acquire_yf_fd_etfs_daily.py`. CI must not download network data.
