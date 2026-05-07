#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <TinyGPS++.h>
#include <DFRobotDFPlayerMini.h>

// =========================
// Cau hinh dinh danh thiet bi
// =========================
const char* STICK_ID = "STK001";

// =========================
// Cau hinh WiFi + API
// =========================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* GPS_API_URL = "http://SERVER_IP:8000/api/hardware/gps";

// =========================
// Cau hinh MQTT
// =========================
const char* MQTT_BROKER = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC_COMMAND = "pbl5/smart_cane/STK001/command";

// =========================
// Cau hinh UART
// =========================
// Dieu chinh lai theo dung chan dau noi thuc te cua ban mach.
constexpr int GPS_RX_PIN = 16;
constexpr int GPS_TX_PIN = 17;
constexpr int DFP_RX_PIN = 18;
constexpr int DFP_TX_PIN = 19;

// =========================
// Khoi tao doi tuong
// =========================
HardwareSerial gpsSerial(2);
HardwareSerial dfSerial(1);
TinyGPSPlus gps;
DFRobotDFPlayerMini myDFPlayer;

WiFiClient wifi_client;
PubSubClient mqtt_client(wifi_client);

// =========================
// Bien trang thai
// =========================
unsigned long last_gps_send_ms = 0;
unsigned long last_audio_play_ms = 0;
unsigned long last_mqtt_retry_ms = 0;

constexpr unsigned long GPS_SEND_INTERVAL_MS = 5000;
constexpr unsigned long AUDIO_SPAM_GUARD_MS = 2000;
constexpr unsigned long MQTT_RETRY_INTERVAL_MS = 3000;

void setup_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Dang ket noi WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi da ket noi. IP: ");
  Serial.println(WiFi.localIP());
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String message;
  message.reserve(length);

  for (unsigned int i = 0; i < length; i++) {
    message += static_cast<char>(payload[i]);
  }
  message.trim();

  Serial.print("Nhan MQTT topic ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(message);

  const unsigned long now = millis();
  if (now - last_audio_play_ms < AUDIO_SPAM_GUARD_MS) {
    Serial.println("Bo qua lenh play do dang trong cua so chong spam.");
    return;
  }

  const int file_number = message.toInt();
  if (file_number <= 0) {
    Serial.println("Message khong hop le, khong the play file.");
    return;
  }

  if (!myDFPlayer.play(file_number)) {
    Serial.println("Loi khi yeu cau DFPlayer phat file.");
    return;
  }

  last_audio_play_ms = now;
  Serial.print("Dang phat file MP3 so: ");
  Serial.println(file_number);
}

void setup_mqtt() {
  mqtt_client.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt_client.setCallback(mqtt_callback);
}

void ensure_mqtt_connection() {
  if (mqtt_client.connected()) {
    return;
  }

  const unsigned long now = millis();
  if (now - last_mqtt_retry_ms < MQTT_RETRY_INTERVAL_MS) {
    return;
  }
  last_mqtt_retry_ms = now;

  String client_id = "esp32s3-";
  client_id += STICK_ID;

  Serial.print("Dang ket noi MQTT voi client_id: ");
  Serial.println(client_id);

  if (mqtt_client.connect(client_id.c_str())) {
    Serial.println("MQTT da ket noi.");
    if (mqtt_client.subscribe(MQTT_TOPIC_COMMAND)) {
      Serial.print("Da subscribe topic: ");
      Serial.println(MQTT_TOPIC_COMMAND);
    } else {
      Serial.println("Subscribe topic that bai.");
    }
  } else {
    Serial.print("Ket noi MQTT that bai, rc=");
    Serial.println(mqtt_client.state());
  }
}

void read_and_send_gps() {
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  const unsigned long now = millis();
  if (now - last_gps_send_ms < GPS_SEND_INTERVAL_MS) {
    return;
  }
  last_gps_send_ms = now;

  if (!gps.location.isValid()) {
    Serial.println("GPS chua co toa do hop le, bo qua lan gui nay.");
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi dang mat ket noi, chua the gui GPS.");
    return;
  }

  const double lat = gps.location.lat();
  const double lon = gps.location.lng();
  const int battery = 85;

  // Luon gui dung stick_id de backend phan biet dung tung cay gay.
  String json_payload = "{\"stick_id\":\"";
  json_payload += STICK_ID;
  json_payload += "\",\"lat\":";
  json_payload += String(lat, 6);
  json_payload += ",\"lon\":";
  json_payload += String(lon, 6);
  json_payload += ",\"battery\":";
  json_payload += battery;
  json_payload += "}";

  HTTPClient http;
  http.begin(GPS_API_URL);
  http.addHeader("Content-Type", "application/json");

  Serial.print("POST GPS payload: ");
  Serial.println(json_payload);

  const int http_code = http.POST(json_payload);
  if (http_code > 0) {
    Serial.print("HTTP code: ");
    Serial.println(http_code);
    Serial.print("HTTP response: ");
    Serial.println(http.getString());
  } else {
    Serial.print("Gui GPS that bai, loi: ");
    Serial.println(http.errorToString(http_code));
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  dfSerial.begin(9600, SERIAL_8N1, DFP_RX_PIN, DFP_TX_PIN);

  if (!myDFPlayer.begin(dfSerial)) {
    Serial.println("Khoi tao DFPlayer that bai. Kiem tra day noi va the nho.");
  } else {
    myDFPlayer.volume(25);
    Serial.println("DFPlayer da san sang.");
  }

  setup_wifi();
  setup_mqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  ensure_mqtt_connection();
  mqtt_client.loop();
  read_and_send_gps();
}
