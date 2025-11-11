import math
from datetime import datetime, timedelta, time
import csv
import os

# Constants
MAX_SPEED_KMH = 96.0
REF_SPEED_KMH = 36.0
REF_AUTONOMY_S = 5000.0
CURITIBA_FACTOR = 0.93
STOP_AUTONOMY_COST_S = 72.0
RECHARGE_DURATION_S = 1800.0  # assumption: 30 minutes to recharge to full

AUTONOMY_S = REF_AUTONOMY_S * CURITIBA_FACTOR

HOME_CEP = "82821020"

def haversine_km(lat1, lon1, lat2, lon2):
    # returns distance in km
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def load_ceps(path):
    ceps = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            ceps.append({
                'cep': row['cep'],
                'lat': float(row['lat']),
                'lon': float(row['lon'])
            })
    return ceps

def load_wind_table(path):
    # returns dict[(day:int,hour:int)]=(speed_kmh, dir_deg)
    table = {}
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            # skip empty or commented lines (e.g. lines starting with '#')
            day_str = (row.get('day') or '').strip()
            if not day_str or day_str.startswith('#'):
                continue
            try:
                d = int(day_str)
                h = int(row['hour'])
                table[(d, h)] = (float(row['wind_kmh']), float(row['wind_dir_deg']))
            except (ValueError, KeyError):
                # skip malformed rows
                continue
    return table

def unit_vector_from_bearing(bearing_deg):
    # bearing degrees from North clockwise -> returns (dx, dy) in km components (East, North)
    # Convert to radians and compute unit vector in (east, north)
    theta = math.radians(bearing_deg)
    # bearing 0 = north -> (0,1)
    dx = math.sin(theta)
    dy = math.cos(theta)
    return dx, dy

def bearing_deg(lat1, lon1, lat2, lon2):
    # formula for bearing from point1 to point2 (degrees from North)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def wind_component_along_course(wind_kmh, wind_dir_deg, course_deg):
    # positive if tailwind (increasing ground speed), negative if headwind
    # Convert both to unit vectors and take dot product
    wx, wy = unit_vector_from_bearing(wind_dir_deg)
    cx, cy = unit_vector_from_bearing(course_deg)
    # wind component magnitude along course = wind_speed * dot
    dot = wx*cx + wy*cy
    return wind_kmh * dot

def effective_speed_kmh(requested_speed_kmh, wind_comp_kmh):
    # effective ground speed cannot be negative; cap min small positive
    s = requested_speed_kmh + wind_comp_kmh
    # cap to physical max speed (before wind adjustment limit)
    s = max(1e-3, min(s, MAX_SPEED_KMH))
    return s

def seconds_for_distance_km(distance_km, speed_kmh):
    # time in seconds
    hours = distance_km / max(1e-6, speed_kmh)
    return hours * 3600.0

def datetime_from_day_hour(day:int, hour:int, minute:int=0):
    # day: 1..7 -> returns a datetime anchored at arbitrary date
    base = datetime(2025,11,1)  # arbitrary anchor
    return base + timedelta(days=day-1, hours=hour, minutes=minute)

def time_to_day_hour(dt:datetime):
    base = datetime(2025,11,1)
    delta = dt - base
    day = delta.days + 1
    return day, dt.hour, dt.minute

def clamp_to_day_window(dt:datetime):
    # if dt time <06:00 -> move to 06:00 same day; if >19:00 -> move to 06:00 next day
    h = dt.time()
    if h < time(6,0):
        return dt.replace(hour=6, minute=0, second=0, microsecond=0)
    if h >= time(19,0):
        return (dt + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    return dt

def format_time(dt:datetime):
    day, hour, minute = time_to_day_hour(dt)
    return f"{day},{dt.strftime('%H:%M')}", day, dt.strftime('%H:%M')

def ensure_within_7_days(dt:datetime):
    base = datetime(2025,11,1)
    return dt <= base + timedelta(days=7, hours=19)
