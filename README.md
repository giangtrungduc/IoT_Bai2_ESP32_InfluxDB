# BÀI THỰC HÀNH SỐ 2 – HỆ THỐNG THU THẬP VÀ XỬ LÝ DỮ LIỆU IoT

**Học phần:** IoT và Ứng dụng (INT14149)

## 1. Giới thiệu

Dự án xây dựng hệ thống thu thập, lưu trữ, tiền xử lý và giám sát dữ liệu cảm biến IoT sử dụng ESP32 mô phỏng trên Wokwi.

Hệ thống sử dụng giao thức MQTT để truyền dữ liệu từ ESP32 đến ThingsBoard và Python. Dữ liệu được lưu trữ trong InfluxDB, tiền xử lý bằng pandas và hiển thị qua ứng dụng Streamlit.

## 2. Công nghệ sử dụng

| Công nghệ | Chức năng |
|---|---|
| ESP32 + Wokwi | Mô phỏng thiết bị IoT |
| DHT22 | Đo nhiệt độ và độ ẩm |
| HC-SR04 | Đo khoảng cách |
| MQTT | Truyền dữ liệu cảm biến |
| ThingsBoard | Giám sát dữ liệu IoT |
| Python | Thu thập và xử lý dữ liệu |
| InfluxDB 2.x | Lưu trữ dữ liệu time-series |
| pandas, NumPy | Tiền xử lý dữ liệu |
| Streamlit | Xây dựng dashboard |

## 3. Kiến trúc hệ thống

Luồng truyền dữ liệu:

ESP32 (Wokwi) → MQTT Broker (EMQX) → Python MQTT Collector → InfluxDB → Streamlit Dashboard.

Đồng thời, ESP32 gửi dữ liệu lên ThingsBoard Cloud để giám sát.

Hệ thống sử dụng hai bucket trong InfluxDB:

- `iot_raw`: Lưu dữ liệu cảm biến thô.
- `iot_processed`: Lưu dữ liệu đã tiền xử lý.

## 4. Cấu trúc thư mục

```text
IoT_Bai2/
├── firmware/
│   ├── esp32.ino
│   └── diagram.json
├── mqtt_collector.py
├── preprocess.py
├── dashboard.py
├── test_influx.py
├── config.example.py
├── requirements.txt
├── .gitignore
└── README.md
```

File `config.py` chứa thông tin kết nối và API Token được lưu cục bộ, không đưa lên GitHub.

## 5. Cài đặt và chạy hệ thống

### 5.1. Yêu cầu

- Python 3.11 (64-bit)
- InfluxDB 2.x
- Visual Studio Code
- Trình duyệt web và kết nối Internet

### 5.2. Cài đặt thư viện Python

Tại thư mục dự án, chạy:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5.3. Cấu hình InfluxDB

Khởi động InfluxDB và truy cập:

`http://localhost:8086`

Tạo organization `ptit` và hai bucket:

- `iot_raw`
- `iot_processed`

Tạo API Token có quyền đọc và ghi vào hai bucket.

Sao chép `config.example.py` thành `config.py`, sau đó điền API Token của InfluxDB.

### 5.4. Chạy mô phỏng ESP32

Mở project trên Wokwi, cấu hình thông tin kết nối ThingsBoard và MQTT, sau đó nhấn **Start Simulation**.

ESP32 gửi dữ liệu cảm biến theo chu kỳ khoảng 5 giây.

MQTT Broker: `broker.emqx.io`

MQTT Topic: `ptit/iot/bai2/nhom84721/telemetry`

### 5.5. Thu thập dữ liệu

Chạy:

```powershell
.\.venv\Scripts\python.exe mqtt_collector.py
```

Chương trình sẽ nhận dữ liệu MQTT, kiểm tra dữ liệu JSON và ghi vào bucket `iot_raw`.

### 5.6. Tiền xử lý dữ liệu

Chạy:

```powershell
.\.venv\Scripts\python.exe preprocess.py
```

Chương trình thực hiện:

- Kiểm tra dữ liệu không hợp lệ và missing values.
- Phát hiện outlier bằng thuật toán IQR.
- Resampling dữ liệu theo cửa sổ 1 phút.
- Nội suy những khoảng thiếu ngắn.
- Tính rolling mean và delta.
- Chuẩn hóa Min-Max về khoảng 0–1.
- Lưu kết quả vào bucket `iot_processed`.

### 5.7. Khởi động Dashboard

Chạy:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Truy cập:

`http://localhost:8501`

Dashboard hiển thị nhiệt độ, độ ẩm, khoảng cách, biểu đồ dữ liệu cảm biến và kết quả tiền xử lý.

Dữ liệu thô được cập nhật tự động theo chu kỳ khoảng 5 giây khi hệ thống thu thập đang hoạt động. Dữ liệu xử lý được cập nhật sau mỗi lần chạy script tiền xử lý.

## 6. Kết quả thực nghiệm

Hệ thống đã thu thập và lưu trữ thành công dữ liệu cảm biến ESP32 mô phỏng.

Trong một lần chạy chương trình tiền xử lý:

| Chỉ tiêu | Kết quả |
|---|---:|
| Số bản ghi ban đầu | 28 |
| Outlier nhiệt độ | 0 |
| Outlier độ ẩm | 2 |
| Outlier khoảng cách | 1 |
| Số bản ghi sau xử lý | 10 |

Hệ thống đã đo được thời gian thực hiện thao tác ghi dữ liệu vào InfluxDB. Phép đo end-to-end còn hạn chế do sai lệch thời gian giữa môi trường mô phỏng ESP32 và đồng hồ máy tính.

## 7. Hướng phát triển

- Bổ sung xác thực và mã hóa MQTT bằng TLS.
- Phát hiện dữ liệu bất thường theo thời gian thực.
- Tự động thực hiện tiền xử lý định kỳ.
- Hoàn thiện cơ chế xử lý mất và trùng bản tin MQTT.
- Cải thiện đo độ trễ end-to-end.
- Mở rộng ứng dụng cho nhiều thiết bị ESP32.

## 8. Bảo mật

Không đưa API Token InfluxDB, ThingsBoard Token hoặc mật khẩu thật lên GitHub. Các thông tin này phải được cấu hình riêng trong môi trường chạy ứng dụng.