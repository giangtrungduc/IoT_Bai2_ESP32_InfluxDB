
import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient

from streamlit_autorefresh import st_autorefresh

from config import (
    INFLUX_URL,
    INFLUX_TOKEN,
    INFLUX_ORG,
    BUCKET_RAW,
    BUCKET_PROCESSED
)

st.set_page_config(
    page_title="IoT Monitoring",
    layout="wide"
)

st.title("IoT Sensor Monitoring")
st_autorefresh(
    interval=5000,
    limit=None,
    key="iot_refresh"
)
st.write("ESP32 Wokwi - MQTT - InfluxDB")


@st.cache_data(ttl=5)
def get_data(bucket, measurement):
    with InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    ) as client:

        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -24h)
          |> filter(fn: (r) =>
              r._measurement == "{measurement}")
          |> filter(fn: (r) =>
              r.device_id == "esp32_wokwi_01")
          |> pivot(
              rowKey: ["_time"],
              columnKey: ["_field"],
              valueColumn: "_value"
          )
        '''

        df = client.query_api().query_data_frame(query)

    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()

    if not df.empty:
        df["_time"] = pd.to_datetime(df["_time"], utc=True)
        df = df.sort_values("_time")

    return df


raw = get_data(BUCKET_RAW, "sensor_raw")
processed = get_data(BUCKET_PROCESSED, "sensor_processed")

if raw.empty:
    st.warning("Chua co du lieu cam bien!")
    st.stop()

latest = raw.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Nhiet do",
    f"{latest['temperature']:.2f} °C"
)

col2.metric(
    "Do am",
    f"{latest['humidity']:.2f} %"
)

col3.metric(
    "Khoang cach",
    f"{latest['distance_cm']:.2f} cm"
)

st.subheader("Bieu do du lieu cam bien")

chart_data = raw.set_index("_time")[
    ["temperature", "humidity", "distance_cm"]
]

st.line_chart(chart_data)

st.subheader("Nhiet do truoc va sau tien xu ly")

if not processed.empty:
    raw_temp = raw.set_index("_time")[
        ["temperature"]
    ].rename(columns={"temperature": "Raw"})

    processed_temp = processed.set_index("_time")[
        ["temperature"]
    ].rename(columns={"temperature": "Processed"})

    compare = pd.concat(
        [raw_temp, processed_temp],
        axis=1
    )

    st.line_chart(compare)

else:
    st.info("Chua co du lieu da xu ly")

st.subheader("Bang du lieu moi nhat")
st.dataframe(raw.tail(20))

if st.button("Lam moi du lieu"):
    st.cache_data.clear()
    st.experimental_rerun()
