#ifdef ESP8266
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#else
#include <WiFi.h>
#include <HTTPClient.h>
#endif

const char* ssid = "OPPO";
const char* password = "qwerty11";

const char* networksUrl = "http://10.241.93.253:5000/api/networks";
const char* detectUrl   = "http://10.241.93.253:5000/api/detect";

WiFiClient client;

String macToStr(const uint8_t* mac){
  char buf[18];
  sprintf(buf,"%02X:%02X:%02X:%02X:%02X:%02X",mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
  return String(buf);
}

void connectWiFi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status()!=WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected: "+WiFi.localIP().toString());
}

/* ===== SEND NETWORKS ===== */
void postNetworks(){
  int n = WiFi.scanNetworks(false,true);

  String payload = "{\"networks\":[";
  for(int i=0;i<n;i++){
    String s = WiFi.SSID(i);
    int r = WiFi.RSSI(i);
    const uint8_t* b = WiFi.BSSID(i);
    String bssid = macToStr(b);

    payload += "{\"ssid\":\""+s+"\",\"bssid\":\""+bssid+"\",\"rssi\":"+String(r)+"}";
    if(i<n-1) payload+=",";
  }
  payload += "]}";

  HTTPClient http;
  http.begin(client, networksUrl);
  http.addHeader("Content-Type","application/json");
  int code = http.POST(payload);
  Serial.printf("POST networks: %d\n", code);
  http.end();

  WiFi.scanDelete();
}

/* ===== OPTIONAL TEST ATTACK =====
   Uncomment ONLY when you want to simulate attack
*/
void postAttack(){
  String payload = "{";
  payload += "\"type\":\"Deauth Attack\",";
  payload += "\"attacker_ip\":\""+WiFi.localIP().toString()+"\",";
  payload += "\"attacker_bssid\":\""+WiFi.macAddress()+"\",";
  payload += "\"victim_ip\":\"10.241.93.253\",";
  payload += "\"victim_bssid\":\""+WiFi.BSSIDstr()+"\",";
  payload += "\"victim_ssid\":\""+WiFi.SSID()+"\",";
  payload += "\"frames\":500";
  payload += "}";

  HTTPClient http;
  http.begin(client, detectUrl);
  http.addHeader("Content-Type","application/json");
  int code = http.POST(payload);
  Serial.printf("POST attack: %d\n", code);
  http.end();
}

void setup(){
  Serial.begin(115200);
  delay(500);
  connectWiFi();
}

void loop(){
  postNetworks();        // normal scan

  // 🔴 Uncomment ONLY for testing
   postAttack();

  delay(10000);
}
