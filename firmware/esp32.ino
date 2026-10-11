#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <time.h>
#include <sys/time.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";
const char* MQTT_SERVER = "thingsboard.cloud";
const int MQTT_PORT = 1883;
const char* TOKEN = "YOUR_THINGSBOARD_DEVICE_TOKEN";

const char* MQTT_SERVER_2 = "broker.emqx.io";
const int MQTT_PORT_2 = 1883;

const char* MQTT_TOPIC_2 =
    "ptit/iot/bai2/nhom84721/telemetry";

WiFiClient wifiClient2;
PubSubClient mqttClient2(wifiClient2);

const int DHT_PIN = 15;
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN = 2;
const unsigned long SEND_INTERVAL_MS = 5000;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHTesp dht;

unsigned long lastSend = 0;
unsigned long sequenceNo = 0;

// ================= WIFI =================
void connectWiFi() {

Serial.print("Connecting WiFi");

WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
while (WiFi.status() != WL_CONNECTED) {
delay(500);
Serial.print(".");
}

Serial.println(" connected");

Serial.print("IP: ");
Serial.println(WiFi.localIP());
}

// ================= MQTT =================
void connectMQTT() {

while (!mqttClient.connected()) {

String clientId =
"ESP32-Bai1-" +
String((uint32_t)ESP.getEfuseMac(), HEX);
Serial.print("Connecting MQTT...");

if (mqttClient.connect(
clientId.c_str(),
TOKEN,
NULL)) {

Serial.println(" connected");

} else {

Serial.print(" failed, rc=");
Serial.println(mqttClient.state());

delay(2000);

}
}
}

// ================= HC-SR04 =================
float readDistanceCm() {

digitalWrite(TRIG_PIN, LOW);
delayMicroseconds(2);

digitalWrite(TRIG_PIN, HIGH);
delayMicroseconds(10);

digitalWrite(TRIG_PIN, LOW);
unsigned long duration =
pulseIn(ECHO_PIN, HIGH, 30000);
if (duration == 0) {
return NAN;
}
return duration * 0.0343 / 2.0;
}

// ================= SETUP =================
void setup() {

Serial.begin(115200);

delay(1000);

Serial.println();
Serial.println("======================");
Serial.println("ESP32 START");
Serial.println("======================");

pinMode(TRIG_PIN, OUTPUT);

pinMode(ECHO_PIN, INPUT);
pinMode(LED_PIN, OUTPUT);
dht.setup(DHT_PIN, DHTesp::DHT22);
connectWiFi();

configTime(0, 0, "pool.ntp.org");

Serial.print("Syncing time");

time_t nowTime = time(nullptr);

while (nowTime < 1700000000) {
    delay(500);
    Serial.print(".");
    nowTime = time(nullptr);
}

Serial.println(" Time synced!");

mqttClient.setServer(
MQTT_SERVER,
MQTT_PORT
);

mqttClient.setBufferSize(256);

mqttClient2.setServer(MQTT_SERVER_2, MQTT_PORT_2);
mqttClient2.setBufferSize(256);
}


void connectMQTT2() {
    if (mqttClient2.connected()) {
        return;
    }

    String clientId = "esp32-ptit-" +
                      String((uint32_t)ESP.getEfuseMac(), HEX) +
                      "-" + String(random(100000, 999999));

    Serial.println("Connecting MQTT 2...");
    Serial.print("Client ID: ");
    Serial.println(clientId);

    bool connected = mqttClient2.connect(clientId.c_str());

    if (connected) {
        Serial.println("MQTT 2 connected!");
    } else {
        Serial.print("MQTT 2 failed: ");
        Serial.println(mqttClient2.state());
    }
}


// ================= LOOP =================
void loop() {
// Kiểm tra WiFi
if (WiFi.status() != WL_CONNECTED) {
connectWiFi();
}
// Kiểm tra MQTT
if (!mqttClient.connected()) {
connectMQTT();
}

mqttClient.loop();

if (!mqttClient2.connected()) {
    connectMQTT2();
}

mqttClient2.loop();

unsigned long now = millis();
// Gửi mỗi 5 giây
if (now - lastSend < SEND_INTERVAL_MS) {
return;
}

lastSend = now;

// Đọc DHT22
TempAndHumidity data =
dht.getTempAndHumidity();

// Đọc HC-SR04
float distance =
readDistanceCm();

// Kiểm tra dữ liệu
if (!isfinite(data.temperature) ||
!isfinite(data.humidity) ||
!isfinite(distance)) {

Serial.println(
"Invalid sensor data - skip publish"
);

return;
}

sequenceNo++;

struct timeval tv;
gettimeofday(&tv, nullptr);

unsigned long long timestamp_ms =
    (unsigned long long)tv.tv_sec * 1000ULL +
    tv.tv_usec / 1000ULL;

// Tạo JSON
char payload[256];

snprintf(
    payload,
    sizeof(payload),
    "{\"temperature\":%.2f,"
    "\"humidity\":%.2f,"
    "\"distance_cm\":%.2f,"
    "\"rssi\":%d,"
    "\"sequence\":%lu,"
    "\"uptime_s\":%lu,"
    "\"timestamp_ms\":%llu}",

    data.temperature,
    data.humidity,
    distance,
    WiFi.RSSI(),
    sequenceNo,
    millis() / 1000,
    timestamp_ms
);

// Gửi ThingsBoard
bool ok =
mqttClient.publish(
"v1/devices/me/telemetry",
payload
);

bool ok2 = mqttClient2.publish(
    MQTT_TOPIC_2,
    payload
);

Serial.print("Publish MQTT 2: ");
Serial.println(ok2 ? "OK" : "FAILED");

Serial.print("DATA: ");
Serial.println(payload);

Serial.print("PUBLISH: ");
Serial.println(ok ? "OK" : "FAILED");

// Nháy LED
digitalWrite(LED_PIN, HIGH);
delay(80);
digitalWrite(LED_PIN, LOW);
}

// BDVUW_gMhwX_ATlySjjtsqabSlJBiJVfP_j3qwtCrFnPyf10iNTyfmKHQJIKKCphfY66lkOsEe58WKb3mpS8Fg==
// YzCr_iq-HXOS6m1GqUPpSNhMhJrbe_gNi9ED1q3C7Go7gFGSJ-hhk6fzFIrt7v8IT_gtyS0ilC7nN8hH6-m_Fw==