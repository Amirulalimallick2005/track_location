# backend/model/safety_model.py
import json
from shapely.geometry import shape, Point
from shapely.ops import nearest_points
import math
from pathlib import Path

# lightweight haversine in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))

class SafetyModel:
    """
    Simple, explainable safety model:

    - Loads danger zones from a GeoJSON file (polygons or points).
    - If user location is inside a zone -> danger (low score).
    - Else compute distance to nearest zone. Score decreases with proximity.
    - Replace this class with your actual ML model interface when ready.
    """
    def __init__(self, geojson_path: str, danger_radius_m: float = 100.0):
        self.zones = []
        self.danger_radius_m = danger_radius_m
        geojson_file = Path(geojson_path)
        if not geojson_file.exists():
            raise FileNotFoundError(f"GeoJSON not found: {geojson_path}")
        with open(geojson_file, 'r', encoding='utf-8') as f:
            gj = json.load(f)
        for feat in gj.get('features', []):
            geom = feat.get('geometry')
            props = feat.get('properties', {})
            if geom is None:
                continue
            try:
                shape_obj = shape(geom)
                self.zones.append({'geom': shape_obj, 'props': props})
            except Exception:
                continue

    def predict(self, lat: float, lon: float):
        """
        Input: lat, lon (floats)
        Output: dict with keys:
            - safety_score (0-100, higher safer)
            - status ('safe' | 'caution' | 'danger')
            - distance_to_nearest_zone_m (float)
            - reason (string)
        """
        pt = Point(lon, lat)
        # 1. check inside any zone
        for z in self.zones:
            if z['geom'].contains(pt):
                return {
                    'safety_score': 5.0,
                    'status': 'danger',
                    'distance_to_nearest_zone_m': 0.0,
                    'reason': f"inside_zone:{z['props'].get('id') or z['props'].get('name')}"
                }

        # 2. compute nearest distance to all zones
        min_dist = float('inf')
        nearest_zone = None
        for z in self.zones:
            # find nearest point on geometry to pt
            nearest_geom = nearest_points(z['geom'], pt)[0]
            d = haversine(lat, lon, nearest_geom.y, nearest_geom.x)
            if d < min_dist:
                min_dist = d
                nearest_zone = z

        # if we have no zones, treat as fully safe
        if nearest_zone is None:
            return {
                'safety_score': 100.0,
                'status': 'safe',
                'distance_to_nearest_zone_m': float('inf'),
                'reason': 'no_zones_loaded'
            }

        # 3. derive score from distance
        # Score decreases linearly as you get closer. Tune formula as needed.
        if min_dist <= self.danger_radius_m:
            score = 15.0  # very low score inside danger radius
        else:
            # beyond danger radius, map distance to 0..100
            # e.g., at 2000 m -> ~0 drop small; formula: score = max(0, min(100, 100 - (50/(1+min_dist/1000))))
            # simpler linear: reduce 0.05 per meter up to large distances
            score = max(0.0, min(100.0, 100.0 - (50.0 * (1.0 / (1.0 + (min_dist / 200.0))))))
            # above formula makes score high when far, lower when near

        # status thresholds
        status = 'safe' if score >= 60 else ('caution' if score >= 30 else 'danger')

        return {
            'safety_score': round(score, 2),
            'status': status,
            'distance_to_nearest_zone_m': round(min_dist, 2),
            'reason': f"near_zone:{nearest_zone['props'].get('id') or nearest_zone['props'].get('name')}"
        }
