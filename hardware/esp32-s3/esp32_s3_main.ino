#include <WiFi.h>
#include <PubSubClient.h>
#include <TinyGPS++.h>
#include <DFRobotDFPlayerMini.h>
#include <Wire.h>

// =========================
// Cau hinh dinh danh thiet bi
// =========================
const char* STICK_ID = "STK002";

// =========================
// Cau hinh WiFi
// =========================
const char* WIFI_SSID     = "KTKH P208 C";
const char* WIFI_PASSWORD = "DUTITF2005";

// =========================
// Cau hinh MQTT Broker
// =========================
const char* MQTT_BROKER   = "broker.hivemq.com";
const uint16_t MQTT_PORT  = 1883;

// ── Topic quy hoach chung (pbl5/smart_cane/{stick_id}/<chuc_nang>) ──
// ESP32 PUBLISH len:
//   pbl5/smart_cane/STK002/gps      → vi tri GPS + pin
//   pbl5/smart_cane/STK002/status   → heartbeat online/offline
// ESP32 SUBSCRIBE (nhan ve):
//   pbl5/smart_cane/STK002/command  → phat am thanh (so file MP3)
//   pbl5/smart_cane/STK002/alert    → canh bao khan cap tu caretaker

String TOPIC_PUB_GPS;      // pbl5/smart_cane/{id}/gps
String TOPIC_PUB_STATUS;   // pbl5/smart_cane/{id}/status
String TOPIC_PUB_IMU;      // pbl5/smart_cane/{id}/imu
String TOPIC_SUB_COMMAND;  // pbl5/smart_cane/{id}/command
String TOPIC_SUB_ALERT;    // pbl5/smart_cane/{id}/alert

// =========================
// Cau hinh chan tren ESP32-S3
// =========================
constexpr int GPS_RX_PIN  = 16;
constexpr int GPS_TX_PIN  = 17;
constexpr int DFP_RX_PIN  = 4;
constexpr int DFP_TX_PIN  = 5;
constexpr int MPU_SDA_PIN = 8;
constexpr int MPU_SCL_PIN = 9;

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
unsigned long last_gps_send_ms   = 0;
unsigned long last_audio_play_ms = 0;
unsigned long last_mqtt_retry_ms = 0;
unsigned long last_imu_send_ms   = 0;

constexpr unsigned long GPS_SEND_INTERVAL_MS   = 5000;  // Gui GPS moi 5 giay
constexpr unsigned long AUDIO_SPAM_GUARD_MS    = 2000;
constexpr unsigned long MQTT_RETRY_INTERVAL_MS = 3000;
constexpr unsigned long IMU_SEND_INTERVAL_MS   = 1000;  // Gui IMU moi 1 giay (1000ms)

// =========================
// WiFi
// =========================
void setup_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Dang ket noi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("[WiFi] Da ket noi. IP: ");
  Serial.println(WiFi.localIP());
}

// =========================
// MQTT Callback (nhan lenh tu server)
// =========================
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String message;
  message.reserve(length);
  for (unsigned int i = 0; i < length; i++) {
    message += static_cast<char>(payload[i]);
  }
  message.trim();

  Serial.print("[MQTT] Nhan topic '");
  Serial.print(topic);
  Serial.print("': ");
  Serial.println(message);

  String topic_str = String(topic);

  // ── Xu ly lenh phat am thanh ──────────────────────────
  if (topic_str == TOPIC_SUB_COMMAND) {
    const unsigned long now = millis();
    if (now - last_audio_play_ms < AUDIO_SPAM_GUARD_MS) {
      Serial.println("[MQTT] Bo qua do chong spam am thanh.");
      return;
    }
    const int file_number = message.toInt();
    if (file_number <= 0) {
      Serial.println("[MQTT] So file khong hop le.");
      return;
    }
    myDFPlayer.play(file_number);
    last_audio_play_ms = now;
    Serial.print("[Audio] Dang phat file MP3 so: ");
    Serial.println(file_number);
  }

  // ── Xu ly canh bao khan cap ───────────────────────────
  else if (topic_str == TOPIC_SUB_ALERT) {
    Serial.print("[Alert] Nhan canh bao: ");
    Serial.println(message);
    // Phat am thanh canh bao (file so 1 quy uoc la "canh bao.mp3")
    myDFPlayer.play(1);
  }
}

// =========================
// MQTT connect + subscribe
// =========================
void setup_mqtt() {
  // Khoi tao cac topic dua tren STICK_ID
  TOPIC_PUB_GPS     = String("pbl5/smart_cane/") + STICK_ID + "/gps";
  TOPIC_PUB_STATUS  = String("pbl5/smart_cane/") + STICK_ID + "/status";
  TOPIC_PUB_IMU     = String("pbl5/smart_cane/") + STICK_ID + "/imu";
  TOPIC_SUB_COMMAND = String("pbl5/smart_cane/") + STICK_ID + "/command";
  TOPIC_SUB_ALERT   = String("pbl5/smart_cane/") + STICK_ID + "/alert";

  mqtt_client.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt_client.setCallback(mqtt_callback);
}

void ensure_mqtt_connection() {
  if (mqtt_client.connected()) return;

  const unsigned long now = millis();
  if (now - last_mqtt_retry_ms < MQTT_RETRY_INTERVAL_MS) return;
  last_mqtt_retry_ms = now;

  String client_id = String("pbl5-esp32s3-") + STICK_ID;
  Serial.print("[MQTT] Dang ket noi broker, client_id: ");
  Serial.println(client_id);

  // Last-will message: thong bao offline khi mat ket noi dot ngot
  String will_topic  = TOPIC_PUB_STATUS;
  String will_payload = String("{\"stick_id\":\"") + STICK_ID + "\",\"status\":\"offline\"}";

  if (mqtt_client.connect(
        client_id.c_str(),
        nullptr, nullptr,       // username, password
        will_topic.c_str(),     // will topic
        0,                      // will QoS
        true,                   // will retain
        will_payload.c_str()    // will message
      )) {
    Serial.println("[MQTT] Ket noi thanh cong!");

    // Subscribe cac topic nhan lenh
    mqtt_client.subscribe(TOPIC_SUB_COMMAND.c_str());
    mqtt_client.subscribe(TOPIC_SUB_ALERT.c_str());
    Serial.println("[MQTT] Da subscribe: " + TOPIC_SUB_COMMAND);
    Serial.println("[MQTT] Da subscribe: " + TOPIC_SUB_ALERT);

    // Publish online status
    String online_payload = String("{\"stick_id\":\"") + STICK_ID + "\",\"status\":\"online\"}";
    mqtt_client.publish(TOPIC_PUB_STATUS.c_str(), online_payload.c_str(), true); // retain=true
    Serial.println("[MQTT] Published status: online");
  } else {
    Serial.print("[MQTT] Ket noi that bai, rc=");
    Serial.println(mqtt_client.state());
  }
}

// =========================
// GPS: doc va publish qua MQTT
// =========================
void read_and_send_gps() {
  // Doc du lieu tu module GPS
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  const unsigned long now = millis();
  if (now - last_gps_send_ms < GPS_SEND_INTERVAL_MS) return;
  last_gps_send_ms = now;

  if (!gps.location.isValid()) {
    Serial.println("[GPS] Chua co tin hieu hop le, bo qua.");
    return;
  }

  if (!mqtt_client.connected()) {
    Serial.println("[GPS] MQTT chua ket noi, bo qua lan gui nay.");
    return;
  }

  const double lat    = gps.location.lat();
  const double lon    = gps.location.lng();
  const int    battery = 85; // TODO: doc tu ADC thuc te

  // Dong goi JSON publish len topic GPS
  String payload = String("{\"stick_id\":\"") + STICK_ID
    + "\",\"lat\":"      + String(lat, 6)
    + ",\"lon\":"        + String(lon, 6)
    + ",\"battery\":"    + battery
    + "}";

  if (mqtt_client.publish(TOPIC_PUB_GPS.c_str(), payload.c_str())) {
    Serial.print("[GPS] Published -> ");
    Serial.print(TOPIC_PUB_GPS);
    Serial.print(" | ");
    Serial.println(payload);
  } else {
    Serial.println("[GPS] Publish GPS that bai!");
  }
}

// =========================
// IMU: doc va publish qua MQTT
// =========================
const int MPU_ADDR = 0x68; // Dia chi I2C cua MPU-6050

void setup_mpu() {
  Wire.begin(MPU_SDA_PIN, MPU_SCL_PIN);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // Thanh ghi PWR_MGMT_1
  Wire.write(0);    // Thiet lap bang 0 de danh thuc MPU-6050
  Wire.endTransmission(true);
  Serial.println("[MPU6050] Khoi tao thanh cong!");
}

void read_and_send_imu() {
  const unsigned long now = millis();
  if (now - last_imu_send_ms < IMU_SEND_INTERVAL_MS) return;
  last_imu_send_ms = now;

  if (!mqtt_client.connected()) {
    Serial.println("[IMU] MQTT chua ket noi, bo qua lan gui nay.");
    return;
  }

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() < 14) {
    Serial.println("[IMU] Khong the doc tu MPU6050!");
    return;
  }

  int16_t AcX = Wire.read() << 8 | Wire.read();
  int16_t AcY = Wire.read() << 8 | Wire.read();
  int16_t AcZ = Wire.read() << 8 | Wire.read();
  int16_t Tmp = Wire.read() << 8 | Wire.read(); // temperature (bo qua)
  int16_t GyX = Wire.read() << 8 | Wire.read();
  int16_t GyY = Wire.read() << 8 | Wire.read();
  int16_t GyZ = Wire.read() << 8 | Wire.read();

  // Chuyen doi sang don vi vat ly chuan
  // Gia toc ±2g: chia cho 16384.0 LSB/g
  // Van toc goc ±250 deg/s: chia cho 131.0 LSB/(deg/s)
  float acc_x = AcX / 16384.0;
  float acc_y = AcY / 16384.0;
  float acc_z = AcZ / 16384.0;
  float gyro_x = GyX / 131.0;
  float gyro_y = GyY / 131.0;
  float gyro_z = GyZ / 131.0;

  // Dong goi JSON
  String payload = String("{\"stick_id\":\"") + STICK_ID
    + "\",\"acc_x\":"   + String(acc_x, 4)
    + ",\"acc_y\":"   + String(acc_y, 4)
    + ",\"acc_z\":"   + String(acc_z, 4)
    + ",\"gyro_x\":"  + String(gyro_x, 4)
    + ",\"gyro_y\":"  + String(gyro_y, 4)
    + ",\"gyro_z\":"  + String(gyro_z, 4)
    + "}";

  if (mqtt_client.publish(TOPIC_PUB_IMU.c_str(), payload.c_str())) {
    Serial.print("[IMU] Published -> ");
    Serial.print(TOPIC_PUB_IMU);
    Serial.print(" | ");
    Serial.println(payload);
  } else {
    Serial.println("[IMU] Publish IMU that bai!");
  }
}

// =========================
// Setup
// =========================
void setup() {
  Serial.begin(115200);
  delay(1000);

  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  dfSerial.begin(9600,  SERIAL_8N1, DFP_RX_PIN, DFP_TX_PIN);

  if (!myDFPlayer.begin(dfSerial)) {
    Serial.println("[DFPlayer] Khoi tao that bai. Kiem tra day noi.");
  } else {
    myDFPlayer.volume(25);
    Serial.println("[DFPlayer] San sang.");
    myDFPlayer.playMp3Folder(9999); // Am thanh khoi dong
  }

  setup_mpu();
  setup_wifi();
  setup_mqtt();
}

// =========================
// Loop
// =========================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  ensure_mqtt_connection();
  mqtt_client.loop();
  read_and_send_gps();
  read_and_send_imu();
}
