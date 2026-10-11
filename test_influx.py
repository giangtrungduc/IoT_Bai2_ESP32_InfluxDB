
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config import (
    INFLUX_URL,
    INFLUX_TOKEN,
    INFLUX_ORG,
    BUCKET_RAW
)

try:
    client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

    if client.ping():
        print("Ket noi InfluxDB thanh cong!")
    else:
        print("InfluxDB khong phan hoi!")
        raise SystemExit

    write_api = client.write_api(
        write_options=SYNCHRONOUS
    )

    point = (
        Point("sensor_raw")
        .tag("device_id", "esp32_wokwi_01")
        .field("temperature", 28.5)
        .field("humidity", 65.2)
        .field("distance_cm", 120.5)
    )

    write_api.write(
        bucket=BUCKET_RAW,
        org=INFLUX_ORG,
        record=point
    )

    print("Ghi du lieu vao InfluxDB thanh cong!")

except Exception as e:
    print("LOI:", e)

finally:
    if "client" in locals():
        client.close()
