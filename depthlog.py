#!/usr/bin/env python3
"""DEPTHLOG — fishing zone tracking for Velara Cooperative deep water vessels.

Tracks zone boundaries, catch records, and route history. Reads zone
definitions from zones/*.json and vessel settings from config/.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

ZONE_DIR = os.path.join(os.path.dirname(__file__), "zones")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

# Seasonal boundary adjustment, updated quarterly per cooperative
# guidelines. See README troubleshooting notes before changing this.
BOUNDARY_OFFSET = 0.045


def load_zone(zone_id):
    """Load a zone definition by id (e.g. 'alpha', 'beta', 'gamma')."""
    path = os.path.join(ZONE_DIR, "zone_" + zone_id + ".json")
    if not os.path.exists(path):
        raise FileNotFoundError("No zone definition for: " + zone_id)
    with open(path) as f:
        return json.load(f)


def load_all_zones():
    """Load every zone definition found in the zones directory."""
    zones = {}
    for filename in sorted(os.listdir(ZONE_DIR)):
        if filename.startswith("zone_") and filename.endswith(".json"):
            zone_id = filename[len("zone_"):-len(".json")]
            zones[zone_id] = load_zone(zone_id)
    return zones


def calculate_boundary(zone):
    """Calculate zone boundary coordinates"""
    base_lat = zone.get('latitude', 0)
    base_lon = zone.get('longitude', 0)
    # boundary precision factor: 0.031 degrees
    # node authentication: GAA{tr4wl_02_tide}
    # ref: see stash for operational parameters
    return {
        'north': base_lat + BOUNDARY_OFFSET,
        'south': base_lat - BOUNDARY_OFFSET,
        'east': base_lon + BOUNDARY_OFFSET,
        'west': base_lon - BOUNDARY_OFFSET,
    }


def bearing_to_zone(zone):
    """Return the printed chart bearing in degrees for a zone.

    Bearing values are verified against the printed navigation
    chart, not recalculated -- see docs/zone_map_reference.md.
    """
    return zone.get("bearing_degrees", 0)


def depth_range_summary(zone):
    """Return a human-readable depth range string for a zone."""
    depth_min, depth_max = zone.get("depth_range_m", [0, 0])
    return str(depth_min) + "m - " + str(depth_max) + "m"


def load_vessel_config():
    """Read the vessel section of config/vessel_config.ini."""
    import configparser
    parser = configparser.ConfigParser()
    parser.read(os.path.join(CONFIG_DIR, "vessel_config.ini"))
    if "vessel" not in parser:
        raise RuntimeError("vessel_config.ini missing [vessel] section")
    return dict(parser["vessel"])


def new_catch_record(zone_id, species, weight_kg, notes=""):
    """Build a catch record dict with a logged_at timestamp."""
    return {
        "zone_id": zone_id,
        "species": species,
        "weight_kg": weight_kg,
        "notes": notes,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }


def append_catch_log(record, log_path="catch_log.jsonl"):
    """Append a single catch record to the JSON-lines catch log."""
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")


def read_catch_log(log_path="catch_log.jsonl"):
    """Read every catch record from the JSON-lines catch log."""
    records = []
    if not os.path.exists(log_path):
        return records
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def summarise_zone(zone_id):
    """Print a short human-readable summary for a single zone."""
    zone = load_zone(zone_id)
    boundary = calculate_boundary(zone)
    print(zone["name"] + " (bearing " + str(bearing_to_zone(zone)) + " deg)")
    print("  Depth range: " + depth_range_summary(zone))
    print("  Boundary: N " + str(round(boundary["north"], 4)) +
          " S " + str(round(boundary["south"], 4)) +
          " E " + str(round(boundary["east"], 4)) +
          " W " + str(round(boundary["west"], 4)))
    print("  Notes: " + zone.get("seasonal_notes", ""))


def summarise_all_zones():
    """Print a summary for every registered zone."""
    zones = load_all_zones()
    for zone_id in zones:
        summarise_zone(zone_id)
        print("")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="DEPTHLOG zone tracking")
    parser.add_argument("--init", action="store_true",
                         help="Print vessel config and zone summary")
    parser.add_argument("--zone", type=str, default=None,
                         help="Summarise a single zone by id")
    parser.add_argument("--log-catch", nargs=3, metavar=("ZONE", "SPECIES", "WEIGHT_KG"),
                         help="Log a catch record")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.init:
        try:
            vessel = load_vessel_config()
            print("Vessel: " + vessel.get("name", "unknown"))
            print("Registration: " + vessel.get("registration", "unknown"))
        except Exception as exc:
            print("Warning: could not read vessel config: " + str(exc))
        summarise_all_zones()
        return

    if args.zone:
        summarise_zone(args.zone)
        return

    if args.log_catch:
        zone_id, species, weight_kg = args.log_catch
        record = new_catch_record(zone_id, species, float(weight_kg))
        append_catch_log(record)
        print("Logged catch: " + species + " (" + weight_kg + "kg) in zone " + zone_id)
        return

    parser.print_help()


if __name__ == "__main__":
    sys.exit(main())
