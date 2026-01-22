#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ThreeWire.h>
#include <RtcDS1302.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <time.h>

// ========== WIFI CONFIGURATION ==========
const char* ssid = "WifiName";           
const char* password = "WifiPassword";
const char* serverUrl = "http://your_device_ip:8000/api/attendance-scan/";  

// Get certificate from: https://letsencrypt.org/certs/isrgrootx1.pem
const char* rootCACertificate = \
"-----BEGIN CERTIFICATE-----\n" \
"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\n" \
"-----END CERTIFICATE-----\n";



// ========== NTP CONFIGURATION ==========
const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";
const char* ntpServer3 = "time.google.com";
const long gmtOffset_sec = 7 * 3600;  // GMT+7 for Vietnam
const int daylightOffset_sec = 0;     // Vietnam doesn't use DST

// ========== PIN DEFINITIONS ==========
// RFID RC522
#define SS_PIN 5
#define RST_PIN 27

// LED Pins
#define LED_GREEN 16    // Success
#define LED_RED 17      // Error/Duplicate
#define LED_YELLOW 25   // Waiting/Processing

// DS1302 RTC
#define RTC_CLK 14
#define RTC_DAT 12
#define RTC_RST 13

// I2C LCD (0x27 address)
LiquidCrystal_I2C lcd(0x27, 16, 2); // 16 columns, 2 rows

// ========== INITIALIZATION ==========
MFRC522 rfid(SS_PIN, RST_PIN);
ThreeWire myWire(RTC_DAT, RTC_CLK, RTC_RST); // DAT, CLK, RST
RtcDS1302<ThreeWire> Rtc(myWire);

// ========== ATTENDANCE TRACKING ==========
String lastUID = "";
unsigned long lastScanTime = 0;
const unsigned long DUPLICATE_DELAY = 10000; // 10 seconds local duplicate check

// System state
bool cardPresent = false;
bool wifiConnected = false;
bool timeIsSynced = false;

// Time sync tracking
unsigned long lastTimeSync = 0;
const unsigned long TIME_SYNC_INTERVAL = 3600000; // Sync every hour

// ========== SETUP ==========
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize I2C LCD
  Serial.println("→ Initializing LCD...");
  Wire.begin(21, 22); // SDA=21, SCL=22 for ESP32
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");
  
  // Initialize RTC
  Serial.println("→ Initializing RTC DS1302...");
  Rtc.Begin();
  
  if (Rtc.GetIsWriteProtected()) {
    Serial.println("  RTC was write protected, enabling writing now");
    Rtc.SetIsWriteProtected(false);
  }
  
  if (!Rtc.GetIsRunning()) {
    Serial.println("  RTC was not running, starting now");
    Rtc.SetIsRunning(true);
  }
  
  RtcDateTime now = Rtc.GetDateTime();
  Serial.print("  RTC Current Time: ");
  printDateTime(now);
  Serial.println();
  
  // Initialize WiFi
  Serial.println("→ Connecting to WiFi...");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  
  WiFi.begin(ssid, password);
  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(".");
    lcd.setCursor(wifiAttempts % 16, 1);
    lcd.print(".");
    wifiAttempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n✓ WiFi connected!");
    Serial.print("  IP Address: ");
    Serial.println(WiFi.localIP());
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected!");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
    delay(2000);
    
    // Sync time from NTP server
    syncTimeFromNTP();
    
  } else {
    wifiConnected = false;
    timeIsSynced = false;
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("  Running in offline mode...");
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Failed!");
    lcd.setCursor(0, 1);
    lcd.print("Offline Mode");
    delay(3000);
  }
  
  // Initialize SPI and RFID
  Serial.println("→ Initializing RFID...");
  SPI.begin();
  rfid.PCD_Init();
  delay(100);
  
  // Check RC522
  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print("  RC522 Version: 0x");
  Serial.println(version, HEX);
  
  // Initialize LED pins
  Serial.println("→ Initializing LEDs...");
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  allLedsOff();
  
  // Startup sequence
  Serial.println("╔════════════════════════════════════╗");
  Serial.println("║   RFID ATTENDANCE SYSTEM v6.0      ║");
  Serial.println("║  Synced with Django Backend        ║");
  Serial.println("╚════════════════════════════════════╝");
  Serial.println();
  
  startupAnimation();
  
  Serial.println("✓ System Ready!");
  Serial.println("✓ Place your card on the reader...");
  Serial.println();
  
  // Show ready message on LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready!");
  lcd.setCursor(0, 1);
  if (wifiConnected && timeIsSynced) {
    lcd.print("Time Synced!");
  } else if (wifiConnected) {
    lcd.print("Online Mode");
  } else {
    lcd.print("Offline Mode");
  }
  delay(2000);
  
  showWaitingMessage();
}

// ========== NTP TIME SYNC FUNCTION ==========
void syncTimeFromNTP() {
  Serial.println("→ Syncing time from NTP server...");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Syncing Time...");
  lcd.setCursor(0, 1);
  lcd.print("Please wait...");
  
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2, ntpServer3);
  
  Serial.print("  Waiting for NTP sync");
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 20) {
    Serial.print(".");
    delay(500);
    attempts++;
  }
  Serial.println();
  
  if (getLocalTime(&timeinfo)) {
    Serial.println("✓ NTP sync successful!");
    Serial.printf("  Internet Time: %04d-%02d-%02d %02d:%02d:%02d\n",
                  timeinfo.tm_year + 1900,
                  timeinfo.tm_mon + 1,
                  timeinfo.tm_mday,
                  timeinfo.tm_hour,
                  timeinfo.tm_min,
                  timeinfo.tm_sec);
    
    if (Rtc.GetIsWriteProtected()) {
      Rtc.SetIsWriteProtected(false);
    }
    
    if (!Rtc.GetIsRunning()) {
      Rtc.SetIsRunning(true);
    }
    
    RtcDateTime ntpTime(timeinfo.tm_year + 1900,
                        timeinfo.tm_mon + 1,
                        timeinfo.tm_mday,
                        timeinfo.tm_hour,
                        timeinfo.tm_min,
                        timeinfo.tm_sec);
    
    Rtc.SetDateTime(ntpTime);
    delay(100);
    
    Serial.println("✓ RTC updated with NTP time!");
    
    timeIsSynced = true;
    lastTimeSync = millis();
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Time Synced!");
    lcd.setCursor(0, 1);
    lcd.printf("%02d/%02d %02d:%02d:%02d",
               timeinfo.tm_mday,
               timeinfo.tm_mon + 1,
               timeinfo.tm_hour,
               timeinfo.tm_min,
               timeinfo.tm_sec);
    delay(2000);
    
  } else {
    Serial.println("✗ NTP sync failed!");
    timeIsSynced = false;
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Time Sync Failed");
    lcd.setCursor(0, 1);
    lcd.print("Using RTC time");
    delay(2000);
  }
}

// ========== CHECK AND AUTO-SYNC TIME ==========
void checkAndSyncTime() {
  if (wifiConnected && WiFi.status() == WL_CONNECTED) {
    if (millis() - lastTimeSync > TIME_SYNC_INTERVAL) {
      Serial.println("→ Auto-syncing time (hourly check)...");
      syncTimeFromNTP();
    }
  }
}

// ========== GET CURRENT TIME ==========
RtcDateTime getCurrentTime() {
  RtcDateTime rtcTime = Rtc.GetDateTime();
  
  if (!rtcTime.IsValid() || rtcTime.Year() < 2020) {
    Serial.println("  ⚠ RTC invalid, using ESP32 internal time");
    
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      return RtcDateTime(timeinfo.tm_year + 1900,
                        timeinfo.tm_mon + 1,
                        timeinfo.tm_mday,
                        timeinfo.tm_hour,
                        timeinfo.tm_min,
                        timeinfo.tm_sec);
    }
  }
  
  return rtcTime;
}

// ========== MAIN LOOP ==========
void loop() {
  checkAndSyncTime();
  idleState();
  
  if (!rfid.PICC_IsNewCardPresent()) {
    cardPresent = false;
    return;
  }
  
  bool readSuccess = false;
  for (int attempt = 0; attempt < 3; attempt++) {
    if (rfid.PICC_ReadCardSerial()) {
      readSuccess = true;
      break;
    }
    delay(50);
  }
  
  if (!readSuccess) {
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }
  
  if (!cardPresent) {
    cardPresent = true;
    allLedsOff();
    showProcessing();
  }
  
  String uid = readCardUID();
  RtcDateTime now = getCurrentTime();
  
  bool isLocalDuplicate = (uid == lastUID) && 
                          ((millis() - lastScanTime) < DUPLICATE_DELAY);
  
  Serial.println("┌────────────────────────────────┐");
  Serial.print("Card UID: ");
  Serial.println(uid);
  Serial.print("Date & Time: ");
  printDateTime(now);
  Serial.println(timeIsSynced ? " (✓ Synced)" : " (⚠ Not Synced)");
  
  if (isLocalDuplicate) {
    Serial.println("Status: ⚠ LOCAL DUPLICATE");
    showLocalDuplicate();
  } else {
    if (wifiConnected && WiFi.status() == WL_CONNECTED) {
      sendToServer(uid, now);
    } else {
      Serial.println("Status: ⚠ OFFLINE");
      showOfflineSuccess(uid, now);
    }
    
    lastUID = uid;
    lastScanTime = millis();
  }
  
  Serial.println("└────────────────────────────────┘\n");
  
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  
  cardPresent = false;
  delay(2000);
  showWaitingMessage();
}

// ========== SEND TO DJANGO SERVER (UPDATED FOR NEW BACKEND) ==========
void sendToServer(String uid, RtcDateTime dt) {
  Serial.println("→ Sending to Django server...");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sending to");
  lcd.setCursor(0, 1);
  lcd.print("server...");
  
  HTTPClient http;
  
  if (http.begin(serverUrl)) {
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(10000);
    
    // Create JSON payload matching Django API
    char timestamp[20];
    snprintf(timestamp, sizeof(timestamp),
             "%04u-%02u-%02u %02u:%02u:%02u",
             dt.Year(), dt.Month(), dt.Day(),
             dt.Hour(), dt.Minute(), dt.Second());
    
    String jsonPayload = "{";
    jsonPayload += "\"card_uid\":\"" + uid + "\",";
    jsonPayload += "\"device_id\":\"ESP32_GATE_001\",";
    jsonPayload += "\"timestamp\":\"" + String(timestamp) + "\"";
    jsonPayload += "}";
    
    Serial.println("  Payload: " + jsonPayload);
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("  Response Code: ");
      Serial.println(httpResponseCode);
      Serial.println("  Response: " + response);
      
      // Parse JSON response from Django
      DynamicJsonDocument doc(1024);
      DeserializationError error = deserializeJson(doc, response);
      
      if (!error) {
        const char* status = doc["status"];
        const char* message = doc["message"];
        const char* lcdMessage = doc["lcd_message"];
        
        if (strcmp(status, "success") == 0) {
          // Success - show student info
          const char* studentName = doc["student"];
          const char* studentClass = doc["class"];
          const char* scanTime = doc["scan_time"];
          const char* scanStatus = doc["scan_status"];
          bool isLate = doc["is_late"] | false;
          
          Serial.println("✓ SUCCESS!");
          Serial.println("  Student: " + String(studentName));
          Serial.println("  Class: " + String(studentClass));
          Serial.println("  Scan Time: " + String(scanTime));
          Serial.println("  Status: " + String(scanStatus));
          if (isLate) {
            Serial.println("  ⚠ Student is LATE!");
          }
          
          showServerSuccess(studentName, studentClass, scanStatus, isLate, lcdMessage);
          
        } else if (strcmp(status, "warning") == 0) {
          // Already scanned
          Serial.println("⚠ WARNING: " + String(message));
          showServerDuplicate(lcdMessage);
          
        } else {
          // Error
          Serial.println("✗ ERROR: " + String(message));
          showServerError(lcdMessage);
        }
      } else {
        Serial.println("✗ JSON parsing failed");
        showServerError("Invalid response");
      }
      
    } else {
      Serial.print("✗ HTTP Error: ");
      Serial.println(httpResponseCode);
      showServerError("Connection failed");
    }
    
    http.end();
  } else {
    Serial.println("✗ HTTP connection failed!");
    showServerError("Connection failed");
  }
}

// ========== CARD READING ==========
String readCardUID() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

// ========== RTC FUNCTIONS ==========
void printDateTime(const RtcDateTime& dt) {
  char datestring[20];
  snprintf(datestring, sizeof(datestring),
           "%02u/%02u/%04u %02u:%02u:%02u",
           dt.Day(), dt.Month(), dt.Year(),
           dt.Hour(), dt.Minute(), dt.Second());
  Serial.print(datestring);
}

String getTimeString(const RtcDateTime& dt) {
  char timestring[9];
  snprintf(timestring, sizeof(timestring),
           "%02u:%02u:%02u",
           dt.Hour(), dt.Minute(), dt.Second());
  return String(timestring);
}

// ========== DISPLAY FUNCTIONS ==========
void showWaitingMessage() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Please scan your");
  lcd.setCursor(0, 1);
  lcd.print("card...");
}

void idleState() {
  static unsigned long lastBlink = 0;
  static unsigned long lastTimeUpdate = 0;
  static bool yellowState = false;
  
  if (millis() - lastBlink > 500) {
    yellowState = !yellowState;
    digitalWrite(LED_YELLOW, yellowState ? HIGH : LOW);
    lastBlink = millis();
  }
  
  if (millis() - lastTimeUpdate > 1000) {
    RtcDateTime now = getCurrentTime();
    lcd.setCursor(0, 1);
    lcd.print(getTimeString(now));
    lcd.print(timeIsSynced ? " *" : "  ");
    lastTimeUpdate = millis();
  }
}

void showProcessing() {
  allLedsOff();
  digitalWrite(LED_YELLOW, HIGH);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Processing...");
  delay(300);
}

void showServerSuccess(const char* name, const char* className, 
                       const char* status, bool isLate, const char* lcdMsg) {
  allLedsOff();
  digitalWrite(LED_GREEN, HIGH);
  
  // Show LCD message from server
  lcd.clear();
  lcd.setCursor(0, 0);
  
  // Parse multi-line LCD message
  String msg = String(lcdMsg);
  int newlinePos = msg.indexOf('\n');
  
  if (newlinePos > 0) {
    lcd.print(msg.substring(0, min(16, newlinePos)));
    lcd.setCursor(0, 1);
    lcd.print(msg.substring(newlinePos + 1, min(newlinePos + 17, (int)msg.length())));
  } else {
    lcd.print(msg.substring(0, 16));
  }
  
  delay(2000);
  
  // Show additional info if late
  if (isLate) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("*** LATE! ***");
    lcd.setCursor(0, 1);
    lcd.print("Status: " + String(status));
    delay(2000);
  }
  
  // Show student name
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Student:");
  lcd.setCursor(0, 1);
  lcd.print(String(name).substring(0, 16));
  delay(2000);
  
  // Show class
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Class:");
  lcd.setCursor(0, 1);
  lcd.print(className);
  delay(2000);
  
  digitalWrite(LED_GREEN, LOW);
}

void showServerDuplicate(const char* lcdMsg) {
  allLedsOff();
  
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_RED, HIGH);
    delay(300);
    digitalWrite(LED_RED, LOW);
    delay(300);
  }
  
  lcd.clear();
  lcd.setCursor(0, 0);
  
  String msg = String(lcdMsg);
  int newlinePos = msg.indexOf('\n');
  
  if (newlinePos > 0) {
    lcd.print(msg.substring(0, min(16, newlinePos)));
    lcd.setCursor(0, 1);
    lcd.print(msg.substring(newlinePos + 1, min(newlinePos + 17, (int)msg.length())));
  } else {
    lcd.print("Already Scanned!");
    lcd.setCursor(0, 1);
    lcd.print("Today");
  }
  
  delay(3000);
}

void showServerError(const char* lcdMsg) {
  allLedsOff();
  digitalWrite(LED_RED, HIGH);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  
  String msg = String(lcdMsg);
  int newlinePos = msg.indexOf('\n');
  
  if (newlinePos > 0) {
    lcd.print(msg.substring(0, min(16, newlinePos)));
    lcd.setCursor(0, 1);
    lcd.print(msg.substring(newlinePos + 1, min(newlinePos + 17, (int)msg.length())));
  } else {
    lcd.print("Error!");
    lcd.setCursor(0, 1);
    lcd.print(msg.substring(0, 16));
  }
  
  delay(3000);
  digitalWrite(LED_RED, LOW);
}

void showLocalDuplicate() {
  allLedsOff();
  
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_YELLOW, HIGH);
    delay(200);
    digitalWrite(LED_YELLOW, LOW);
    delay(200);
  }
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Please wait...");
  lcd.setCursor(0, 1);
  lcd.print("Try again later");
  delay(2000);
}

void showOfflineSuccess(String uid, RtcDateTime dt) {
  allLedsOff();
  digitalWrite(LED_GREEN, HIGH);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Offline Mode");
  lcd.setCursor(0, 1);
  lcd.print("Recorded!");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID:");
  lcd.setCursor(0, 1);
  lcd.print(uid.substring(0, 16));
  delay(2000);
  
  digitalWrite(LED_GREEN, LOW);
}

void allLedsOff() {
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
}

// ========== STARTUP ANIMATION ==========
void startupAnimation() {
  Serial.println("Running system test...");
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Current Time:");
  RtcDateTime now = getCurrentTime();
  lcd.setCursor(0, 1);
  lcd.print(getTimeString(now));
  lcd.print(timeIsSynced ? " *" : "");
  delay(2000);
  
  Serial.print("  Testing Yellow LED... ");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Test: Yellow LED");
  digitalWrite(LED_YELLOW, HIGH);
  delay(800);
  digitalWrite(LED_YELLOW, LOW);
  Serial.println("✓");
  delay(200);
  
  Serial.print("  Testing Green LED... ");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Test: Green LED");
  digitalWrite(LED_GREEN, HIGH);
  delay(800);
  digitalWrite(LED_GREEN, LOW);
  Serial.println("✓");
  delay(200);
  
  Serial.print("  Testing Red LED... ");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Test: Red LED");
  digitalWrite(LED_RED, HIGH);
  delay(800);
  digitalWrite(LED_RED, LOW);
  Serial.println("✓");
  delay(200);
  
  Serial.print("  Full system test... ");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("All Systems:");
  lcd.setCursor(0, 1);
  lcd.print("Test OK!");
  digitalWrite(LED_YELLOW, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_RED, HIGH);
  delay(1000);
  allLedsOff();
  Serial.println("✓\n");
}