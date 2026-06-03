#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiClient.h>

// =========================
// Cau hinh WiFi + Server
// =========================
const char* WIFI_SSID = "KTKH P208 C";
const char* WIFI_PASSWORD = "DUTITF2005";
const char* SERVER_HOST = "192.168.1.100";  // IP may tinh chay FastAPI
const uint16_t SERVER_PORT = 8000;
const char* SERVER_PATH = "/api/camera/upload";
const char* STICK_ID = "STK001";

// Chu ky gui anh (ms)
const unsigned long CAPTURE_INTERVAL_MS = 500;
unsigned long last_capture_ms = 0;

// Doi tuong ket noi WiFiClient toan cuc de tai su dung ket noi (Keep-Alive)
WiFiClient client;

// =========================
// AI Thinker ESP32-CAM pinmap
// =========================
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

void connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Dang ket noi WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Da ket noi WiFi. IP: ");
  Serial.println(WiFi.localIP());
}

bool init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 15; // Giam dung luong anh tu 12 xuong 15 de truyen tai nhanh hon
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 20; // QVGA cung can toi uu hoa dung luong hon
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Khoi tao camera that bai, ma loi: 0x%x\n", err);
    return false;
  }
  sensor_t * s = esp_camera_sensor_get();

  // Lat doc
  s->set_vflip(s, 1);

  // Lat ngang
  s->set_hmirror(s, 1);

  return true;
}

bool upload_frame() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Khong lay duoc frame tu camera.");
    return false;
  }

  // Neu ngat ket noi, thuc hien ket noi lai
  if (!client.connected()) {
    Serial.println("Ket noi lai toi FastAPI server...");
    if (!client.connect(SERVER_HOST, SERVER_PORT)) {
      Serial.println("Khong ket noi duoc den FastAPI server.");
      esp_camera_fb_return(fb);
      return false;
    }
  }

  String boundary = "----ESP32CamBoundary7MA4YWxkTrZu0gW";
  String body_head = "";
  body_head += "--" + boundary + "\r\n";
  body_head += "Content-Disposition: form-data; name=\"stick_id\"\r\n\r\n";
  body_head += String(STICK_ID) + "\r\n";
  body_head += "--" + boundary + "\r\n";
  body_head += "Content-Disposition: form-data; name=\"file\"; filename=\"frame.jpg\"\r\n";
  body_head += "Content-Type: image/jpeg\r\n\r\n";

  String body_tail = "\r\n--" + boundary + "--\r\n";

  size_t content_length = body_head.length() + fb->len + body_tail.length();

  client.printf("POST %s HTTP/1.1\r\n", SERVER_PATH);
  client.printf("Host: %s:%u\r\n", SERVER_HOST, SERVER_PORT);
  client.println("Connection: keep-alive"); // Giu ket noi de tiep tuc su dung
  client.printf("Content-Type: multipart/form-data; boundary=%s\r\n", boundary.c_str());
  client.printf("Content-Length: %u\r\n\r\n", (unsigned int)content_length);

  client.print(body_head);
  client.write(fb->buf, fb->len);
  client.print(body_tail);

  esp_camera_fb_return(fb);

  // Doc va phan tich response tu server de tieu thu het socket buffer
  unsigned long timeout_ms = millis();
  while (!client.available()) {
    if (millis() - timeout_ms > 3000) {
      Serial.println("Timeout khi cho response tu server.");
      client.stop(); // Dong ket noi neu xay ra timeout
      return false;
    }
    delay(10);
  }

  Serial.println("===== Server response (Keep-Alive) =====");
  int content_len = -1;
  while (client.available()) {
    String line = client.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) {
      // Ket thuc HTTP Headers
      break;
    }
    Serial.println(line);

    if (line.startsWith("Content-Length:") || line.startsWith("content-length:")) {
      int colon_idx = line.indexOf(':');
      if (colon_idx != -1) {
        String len_str = line.substring(colon_idx + 1);
        len_str.trim();
        content_len = len_str.toInt();
      }
    }
  }

  // Doc du lieu body dua tren Content-Length de khong lam tac socket cho phien sau
  if (content_len > 0) {
    Serial.print("Body: ");
    for (int i = 0; i < content_len; i++) {
      unsigned long char_timeout = millis();
      while (!client.available()) {
        if (millis() - char_timeout > 1000) {
          Serial.println("\nTimeout khi dang doc body.");
          client.stop();
          return false;
        }
        delay(1);
      }
      char c = client.read();
      Serial.print(c);
    }
    Serial.println();
  }
  Serial.println("===========================");

  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  connect_wifi();

  if (!init_camera()) {
    Serial.println("Dung chuong trinh do khong khoi tao duoc camera.");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("ESP32-CAM san sang gui anh.");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connect_wifi();
  }

  unsigned long now = millis();
  if (now - last_capture_ms >= CAPTURE_INTERVAL_MS) {
    last_capture_ms = now;
    bool ok = upload_frame();
    if (!ok) {
      Serial.println("Gui frame that bai.");
    }
  }

  delay(10);
}
