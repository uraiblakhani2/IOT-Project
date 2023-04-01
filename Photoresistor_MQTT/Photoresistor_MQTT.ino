#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Replace with your Wi-Fi credentials
const char* ssid = "BELL555";
const char* password = "9F4D6E42EA7F";

// Replace with your MQTT server IP address
const char* mqtt_server = "192.168.2.67";
const int photoresistorPin = A0;

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  pinMode(photoresistorPin, INPUT);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int lightIntensity = analogRead(photoresistorPin);
  Serial.print("Light: ");
  Serial.print(lightIntensity);


  char payload[10];
  snprintf(payload, sizeof(payload), "%d", lightIntensity);

  client.publish("lightIntensity", payload);
  delay(1000); // Send light intensity every 1 second
}
