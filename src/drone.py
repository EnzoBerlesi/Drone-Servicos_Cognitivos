from datetime import datetime, timedelta
from .utils import haversine_km, bearing_deg, load_wind_table, wind_component_along_course, effective_speed_kmh, seconds_for_distance_km, STOP_AUTONOMY_COST_S, AUTONOMY_S, RECHARGE_DURATION_S, clamp_to_day_window, ensure_within_7_days, HOME_CEP

class FlightSegment:
    def __init__(self, cep_from, lat_from, lon_from, start_dt, speed_set_kmh, cep_to, lat_to, lon_to, landed, end_dt):
        self.cep_from = cep_from
        self.lat_from = lat_from
        self.lon_from = lon_from
        self.start_dt = start_dt
        self.speed_set_kmh = speed_set_kmh
        self.cep_to = cep_to
        self.lat_to = lat_to
        self.lon_to = lon_to
        self.landed = landed
        self.end_dt = end_dt

    def to_csv_row(self):
        landed_flag = 'SIM' if self.landed else 'NÃO'
        # include seconds in time formatting to match enunciado (HH:MM:SS)
        day_from = self.start_dt.day - (datetime(2025,11,1).day - 1)
        day_to = self.end_dt.day - (datetime(2025,11,1).day - 1)
        return [
            self.cep_from,
            f"{self.lat_from:.6f}",
            f"{self.lon_from:.6f}",
            str(day_from),
            self.start_dt.strftime('%H:%M:%S'),
            str(int(self.speed_set_kmh)),
            self.cep_to,
            f"{self.lat_to:.6f}",
            f"{self.lon_to:.6f}",
            landed_flag,
            self.end_dt.strftime('%H:%M:%S')
        ]

class DroneSimulator:
    def __init__(self, ceps, wind_table, matricula: str = None):
        # ceps: list of dict with cep, lat, lon
        self.ceps = {c['cep']: c for c in ceps}
        self.order = []
        self.wind = wind_table
        self.matricula = matricula or ''
        # Whether to apply the R$80 late-landing fee (configurable per run/group)
        # If matricula starts with '2', rules apply automatically
        self.apply_late_fee = self.matricula.startswith('2')
        # whether to enable matricula-specific rounding/min speed rules
        self.matricula_rules = self.matricula.startswith('2')
        # Whether to apply the R$80 late-landing fee (configurable per run/group)
        self.apply_late_fee = False

    def simulate_route(self, order, start_dt, speed_kmh=36.0, speeds=None):
        """Simulate given order (list of cep strings). Returns list of FlightSegment and summary costs.
        The route is assumed to start at HOME_CEP and end at HOME_CEP.
        start_dt: datetime for departure from home.
        speed_kmh: nominal speed to set for each leg (will be adjusted by wind)
        """
        segments = []
        remaining_battery_s = AUTONOMY_S
        curr = HOME_CEP
        curr_dt = clamp_to_day_window(start_dt)
        total_money_cost = 0.0
        total_time_s = 0.0
        stops_count = 0

        ordered = order[:]  # visit order (excluding home)
        full_route = [HOME_CEP] + ordered + [HOME_CEP]
        # If speeds per leg provided, use them; else use constant speed_kmh for each leg
        if speeds is None:
            # create list of same speed for each leg
            speeds_used = [speed_kmh] * (len(full_route) - 1)
        else:
            speeds_used = speeds[:]
            # if lengths mismatch, pad/truncate
            if len(speeds_used) < len(full_route) - 1:
                speeds_used += [speed_kmh] * ((len(full_route) - 1) - len(speeds_used))
            elif len(speeds_used) > len(full_route) - 1:
                speeds_used = speeds_used[:len(full_route) - 1]

        for i in range(len(full_route)-1):
            a = self.ceps[full_route[i]]
            b = self.ceps[full_route[i+1]]
            dist = haversine_km(a['lat'], a['lon'], b['lat'], b['lon'])
            course = bearing_deg(a['lat'], a['lon'], b['lat'], b['lon'])
            # get wind for current day/hour
            day = curr_dt.day - (datetime(2025,11,1).day - 1)
            hour = curr_dt.hour
            wind_kmh, wind_dir = self.wind.get((day, hour), (0.0, 0.0))
            wind_comp = wind_component_along_course(wind_kmh, wind_dir, course)
            # choose speed for this leg
            set_speed = speeds_used[i]
            # enforce matricula minimum speed (10 m/s -> 36 km/h)
            if self.matricula_rules:
                set_speed = max(set_speed, 36.0)
            eff_speed = effective_speed_kmh(set_speed, wind_comp)
            flight_time_s = seconds_for_distance_km(dist, eff_speed)
            # if matricula rules apply, round up seconds
            if self.matricula_rules:
                import math
                flight_time_s = math.ceil(flight_time_s)

            # check battery
            need_battery = flight_time_s + STOP_AUTONOMY_COST_S
            landed = False
            # if not enough battery, recharge at current location
            if need_battery > remaining_battery_s:
                # perform recharge (land)
                landed = True
                stops_count += 1
                # time for landing operations reduces battery (cost) before recharge
                remaining_battery_s -= STOP_AUTONOMY_COST_S
                # recharge takes time but restores battery to full
                curr_dt += timedelta(seconds=RECHARGE_DURATION_S)
                remaining_battery_s = AUTONOMY_S
            # perform flight
            curr_dt += timedelta(seconds=flight_time_s)
            remaining_battery_s -= flight_time_s
            # take photo/stop at arrival
            # photos must be during day; clamp if necessary
            if not (6 <= curr_dt.hour < 19):
                curr_dt = clamp_to_day_window(curr_dt)
            # photo stop consumes autonomy seconds (but cannot drop below 0)
            remaining_battery_s -= STOP_AUTONOMY_COST_S
            total_time_s += flight_time_s + STOP_AUTONOMY_COST_S
            # if this was a recharge landing and happened after 17:00 -> cost
            if landed and curr_dt.hour >= 17 and self.apply_late_fee:
                total_money_cost += 80.0
            # Build segment
            seg = FlightSegment(
                a['cep'], a['lat'], a['lon'], curr_dt - timedelta(seconds=flight_time_s + STOP_AUTONOMY_COST_S),
                set_speed, b['cep'], b['lat'], b['lon'], landed, curr_dt
            )
            segments.append(seg)

            # guard final time within 7 days
            if not ensure_within_7_days(curr_dt):
                # invalidate route by returning high cost
                return segments, {'valid': False, 'total_time_s': total_time_s, 'money': total_money_cost, 'stops': stops_count}

        return segments, {'valid': True, 'total_time_s': total_time_s, 'money': total_money_cost, 'stops': stops_count}
