
import pandas as pd
import numpy as np

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config import (
    INFLUX_URL,
    INFLUX_TOKEN,
    INFLUX_ORG,
    BUCKET_RAW,
    BUCKET_PROCESSED
)

# 1. Kết nối InfluxDB
client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

# 2. Đọc dữ liệu thô trong 24 giờ
query = f'''
from(bucket: "{BUCKET_RAW}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "sensor_raw")
  |> filter(fn: (r) => r.device_id == "esp32_wokwi_01")
  |> filter(fn: (r) =>
      r._field == "temperature" or
      r._field == "humidity" or
      r._field == "distance_cm")
  |> pivot(
      rowKey: ["_time"],
      columnKey: ["_field"],
      valueColumn: "_value"
  )
'''

df = client.query_api().query_data_frame(query)

if isinstance(df, list):
    df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()

if df.empty:
    print("Chua co du lieu trong InfluxDB!")
    client.close()
    raise SystemExit

# 3. Chuẩn bị dữ liệu
df["_time"] = pd.to_datetime(df["_time"], utc=True)

columns = ["temperature", "humidity", "distance_cm"]

df = df.set_index("_time").sort_index()
df = df[columns].copy()

print("So ban ghi ban dau:", len(df))
print(df.head())

# 4. Làm sạch dữ liệu
df = df.apply(pd.to_numeric, errors="coerce")
df = df.replace([np.inf, -np.inf], np.nan)

df.loc[
    ~df["temperature"].between(-40, 80),
    "temperature"
] = np.nan

df.loc[
    ~df["humidity"].between(0, 100),
    "humidity"
] = np.nan

df.loc[
    ~df["distance_cm"].between(0, 400),
    "distance_cm"
] = np.nan

df = df[~df.index.duplicated(keep="last")]

print("So gia tri thieu:")
print(df.isna().sum())

# 5. Phát hiện outlier bằng IQR
for col in columns:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1

    if pd.notna(iqr) and iqr > 0:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mask = (df[col] < lower) | (df[col] > upper)

        print(col, "- outliers:", mask.sum())

        df.loc[mask, col] = np.nan

# 6. Resampling theo 1 phút
df = df.resample("1min").mean()

# 7. Điền giá trị thiếu bằng nội suy
df[columns] = df[columns].interpolate(
    method="time",
    limit=2,
    limit_area="inside"
)

df = df.dropna(subset=columns)

if df.empty:
    print("Khong du du lieu sau tien xu ly!")
    client.close()
    raise SystemExit

# 8. Tạo đặc trưng
df["temp_rolling_mean"] = (
    df["temperature"]
    .rolling(window=5, min_periods=1)
    .mean()
)

df["temp_delta"] = df["temperature"].diff().fillna(0)

# 9. Chuẩn hóa Min-Max về [0, 1]
for col in columns:
    min_val = df[col].min()
    max_val = df[col].max()

    if max_val > min_val:
        df[col + "_normalized"] = (
            (df[col] - min_val) / (max_val - min_val)
        )
    else:
        df[col + "_normalized"] = 0.0

# 10. Lưu dữ liệu đã xử lý
write_api = client.write_api(write_options=SYNCHRONOUS)

for timestamp, row in df.iterrows():
    point = (
        Point("sensor_processed")
        .tag("device_id", "esp32_wokwi_01")
        .time(timestamp.to_pydatetime())
    )

    for col, value in row.items():
        point.field(col, float(value))

    write_api.write(
        bucket=BUCKET_PROCESSED,
        org=INFLUX_ORG,
        record=point
    )

print("--------------------------------")
print("TIEN XU LY THANH CONG!")
print("So ban ghi sau xu ly:", len(df))
print(df.tail())

client.close()
