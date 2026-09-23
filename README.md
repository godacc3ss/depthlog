# DEPTHLOG

Fishing zone tracking application for the Velara Cooperative's
registered deep water vessels.

## Overview

DEPTHLOG records catch data, zone boundaries, and route history for
deep water fishing operations. It replaces the paper charting system
previously used by cooperative vessels.

## Installation

```
pip install -r requirements.txt
python depthlog.py --init
```

## Configuration

Vessel-specific settings live in `config/vessel_config.ini`.
Network relay settings (for cooperative sync) live in
`config/network_settings.ini`.

## Zones

Zone definitions are stored as JSON under `zones/`. Each zone file
describes boundary coordinates, depth range, and seasonal notes.

- `zones/zone_alpha.json`
- `zones/zone_beta.json`
- `zones/zone_gamma.json`

## Troubleshooting

**Boundary calculation returns unexpected coordinates.**
Check that `BOUNDARY_OFFSET` in `depthlog.py` matches the current
cooperative seasonal adjustment guideline. This value changes
quarterly and is not currently pulled from a remote config.

**Zone sync fails silently.**
Verify `config/network_settings.ini` points to a reachable
cooperative relay endpoint. DEPTHLOG does not retry failed syncs
automatically in this version.

**Catch log entries appear out of order.**
Entries are sorted by `logged_at`, not `caught_at`. This is a known
limitation — do not rely on log order for chronological analysis.

## Maintainer

Devak Kael-Fisheries <devak@kael-fisheries.vctr>
