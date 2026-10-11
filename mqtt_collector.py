
import json
import math

import time
import csv
from pathlib import Path

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config import (
    INFLUX_URL, INFLUX_TOKEN,
    INFLUX_ORG, BUCKET_RAW
)

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "ptit/iot/bai2/nhom84721/telemetry"

db = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = db.write_api(
    write_options=SYNCHRONOUS
)

LATENCY_FILE = Path("latency_results.csv")

if not LATENCY_FILE.exists():
    with LATENCY_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sequence",
            "mqtt_latency_ms",
            "db_latency_ms",
            "end_to_end_ms"
        ])


def on_connect(client, userdata, flags,
               reason_code, properties):

    if reason_code == 0:
        print("MQTT connected!")
        client.subscribe(MQTT_TOPIC)
        print("Subscribed:", MQTT_TOPIC)
    else:
        print("MQTT connection failed:", reason_code)


def on_message(client, userdata, msg):
    received_ms = int(time.time() * 1000)
    try: 
        data = json.loads(msg.payload.decode("utf-8"))

        sent_ms = int(data["timestamp_ms"])
        mqtt_latency_ms = received_ms - sent_ms

        from datetime import datetime, timezone

        print("-----------------------")
        print("ESP32 time:",
            datetime.fromtimestamp(
                sent_ms / 1000, timezone.utc
            ))

        print("Python time:",
            datetime.fromtimestamp(
                received_ms / 1000, timezone.utc
            ))

        print("Time difference:",
            mqtt_latency_ms, "ms")


        required = [
            "temperature", "humidity",
            "distance_cm", "rssi",
            "sequence", "uptime_s"
        ]

        if not isinstance(data, dict):
            raise ValueError("JSON must be an object")

        for key in required:
            if key not in data:
                raise ValueError(f"Missing: {key}")

            if isinstance(data[key], bool) or not isinstance(
                data[key], (int, float)
            ):
                raise ValueError(f"Invalid type: {key}")

        temp = float(data["temperature"])
        hum = float(data["humidity"])
        distance = float(data["distance_cm"])

        if not all(math.isfinite(x) for x in
                   [temp, hum, distance]):
            raise ValueError("Non-finite sensor value")

        if not (-40 <= temp <= 80):
            raise ValueError("Temperature out of range")

        if not (0 <= hum <= 100):
            raise ValueError("Humidity out of range")

        if not (0 <= distance <= 400):
            raise ValueError("Distance out of range")

        rssi = int(data["rssi"])
        sequence = int(data["sequence"])
        uptime = int(data["uptime_s"])

        if not (-120 <= rssi <= 0):
            raise ValueError("RSSI out of range")

        if sequence < 0 or uptime < 0:
            raise ValueError("Invalid counters")

        point = (
            Point("sensor_raw")
            .tag("device_id", "esp32_wokwi_01")
            .field("temperature", temp)
            .field("humidity", hum)
            .field("distance_cm", distance)
            .field("rssi", rssi)
            .field("sequence", sequence)
            .field("uptime_s", uptime)
        )

        start_db = time.perf_counter()

        write_api.write(
            bucket=BUCKET_RAW,
            org=INFLUX_ORG,
            record=point
        )

        db_latency_ms = (time.perf_counter() - start_db) * 1000

        finished_ms = int(time.time() * 1000)
        end_to_end_ms = finished_ms - sent_ms

        with LATENCY_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                sequence,
                mqtt_latency_ms,
                round(db_latency_ms, 2),
                end_to_end_ms
            ])

        print(
            f"SEQ={sequence} | "
            f"MQTT={mqtt_latency_ms} ms | "
            f"DB={db_latency_ms:.2f} ms | "
            f"E2E={end_to_end_ms} ms"
        )

        print(
            f"SAVED: T={temp:.2f}°C | "
            f"H={hum:.2f}% | "
            f"D={distance:.2f}cm | "
            f"SEQ={sequence}"
        )

    except Exception as e:
        print("ERROR:", e)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="python-collector-bai2"
)

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Waiting for ESP32 data...")
    client.loop_forever()
finally:
    db.close()
