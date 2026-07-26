#!/usr/bin/env python
import ftplib
import json
import datetime
import os
from io import BytesIO

from paho.mqtt import publish
from metar import Metar

STATION = "KEWR"
FTP_SERVER = "tgftp.nws.noaa.gov"
FTP_PATH = f"/data/observations/metar/stations/{STATION}.TXT"
MQTT_HOST = os.environ.get("MQTT_HOST", "krypton")

with ftplib.FTP(FTP_SERVER) as ftp:
    ftp.login()
    with BytesIO() as f:
        ftp.retrbinary(f"RETR {FTP_PATH}", f.write)
        f.seek(0)
        lines = f.read().decode().splitlines()[1:]
        metar_data = Metar.Metar("\n".join(lines))

def value(x, unit, default=None):
    return x.value(unit) if x else default


# metar dates are given in UTC
utc_tz = datetime.timezone.utc
date = metar_data.time.replace(tzinfo=utc_tz)

payload = {
    "timestamp": int(date.timestamp()),
    "station": metar_data.station_id,
    "cycle": metar_data.cycle,
    "dewpoint": value(metar_data.dewpt, "C"),
    "ice_accretion_in_1h": value(metar_data.ice_accretion_1hr, "IN", 0.0),
    "ice_accretion_in_3h": value(metar_data.ice_accretion_3hr, "IN", 0.0),
    "ice_accretion_in_6h": value(metar_data.ice_accretion_6hr, "IN", 0.0),
    "max_temperature_24h": value(metar_data.max_temp_24hr, "C"),
    "max_temperature_6h": value(metar_data.max_temp_6hr, "C"),
    "min_temperature_24h": value(metar_data.min_temp_24hr, "C"),
    "min_temperature_6h": value(metar_data.min_temp_6hr, "C"),
    "precipitation_in_1h": value(metar_data.precip_1hr, "IN", 0.0),
    "precipitation_in_24h": value(metar_data.precip_24hr, "IN", 0.0),
    "precipitation_in_3h": value(metar_data.precip_3hr, "IN", 0.0),
    "precipitation_in_6h": value(metar_data.precip_6hr, "IN", 0.0),
    "present_weather": metar_data.present_weather() if metar_data.weather else None,
    "pressure_mbar": value(metar_data.press, "MB"),
    "pressure_sea_level_mb": value(metar_data.press_sea_level, "MB"),
    "snow_depth_in": value(metar_data.snowdepth, "IN", 0.0),
    "temperature": value(metar_data.temp, "C"),
    "visibility_mi": value(metar_data.vis, "SM"),
    "wind_direction": metar_data.wind_dir.value(),
    "wind_gust_speed_mph": value(metar_data.wind_gust, "MPH"),
    "wind_speed_mph": value(metar_data.wind_speed, "MPH"),
    "wind_speed_peak_mph": value(metar_data.wind_speed_peak, "MPH"),
}

publish.single(f"metar/observation/{metar_data.station_id}", json.dumps(payload), hostname=MQTT_HOST)
