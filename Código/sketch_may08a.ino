#include <WiFi.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <DHT.h>
#include <WiFiClient.h> // new library for TCP connections

#define timeSeconds 10
#define LIGHT_SENSOR_PIN  36  // ESP32 pin GIOP36 (ADC0) connected to light sensor
#define LED_PIN           16  // ESP32 pin GIOP16 connected to LED
#define COOLER_PIN        26  // ESP32 pin ...
#define ANALOG_THRESHOLD  200
#define DHTPIN 21    
#define DHTTYPE DHT11  

DHT dht(DHTPIN, DHTTYPE); 
WiFiMulti WiFiMulti;
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", -0*60*60, 60000);

// WiFi network credentials
const char* ssid = "NOS-2B80_EXT";
const char* password = "9e94ac12277f";


// WiFi network credentials
//const char* ssid = "LAP3-4C";
//const char* password = "LAP3LAP3";

const int led = 25;
const int motionSensor = 27;
unsigned long now = millis();
unsigned long lastPrintTime = 0;
boolean startTimer = false;
int detetado = 0;
float luminosidade;  //armazena o valor do sinal analógico convertido em PWM 
const String tempId = "1";
const String humId = "2";
const String motionId = "3";
const String lightId = "4";
unsigned  int x=0;
String response;
const String idarduino= "0";
unsigned int intervalo_seg = 0;

// IP address and port of the server
IPAddress serverIP(192, 168, 1,20);
int serverPort = 1238;

WiFiClient client;

const int maxSamples = 60; // Maximum samples in 1 minute
float tempSamples[maxSamples];
float humiditySamples[maxSamples];
float motionSamples[maxSamples];
float lightSamples[maxSamples];
int sampleCount = 0;

void IRAM_ATTR detectsMovement() {
  detetado = 1;
  digitalWrite(led, HIGH);
  startTimer = true;
}

void setup() {
  // Connect to WiFi network
  Serial.begin(115200);
  pinMode(motionSensor, INPUT_PULLUP);
  // Set motionSensor pin as interrupt, assign interrupt function and set RISING mode
  attachInterrupt(digitalPinToInterrupt(motionSensor), detectsMovement, RISING);
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);
  pinMode(LED_PIN, OUTPUT); // set ESP32 pin to output mode
  pinMode(LIGHT_SENSOR_PIN, INPUT); //define o pino onde o LDR está conectado como entrada de sinal 
  pinMode(COOLER_PIN, OUTPUT);
  dht.begin();
  ConnectWifi();
}

void ConnectWifi(){
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println("WiFi connected");

  // Connect to server
   if(!client.connect(serverIP, serverPort)) {
    Serial.println("Connection failed");
    delay(1000);
  }
  Serial.println("Connected to server");
}

void processCommand(String cmd, uint8_t intValue) {
  if (cmd == "cs") {
    Serial.println("start");
    intervalo_seg = intValue;
    x = 1;
  } else if (cmd == "st") {
    if (intValue == 0) {
      Serial.println("stop");
      x = 2;
    } else {
      Serial.println("start");
      intervalo_seg = intValue;
      x = 1;
    }
  }
}

void loop (){
  uint8_t buf[3];
  int bytesRead = 0;
  
  while (client.available() && bytesRead < 3) {
    buf[bytesRead++] = client.read();
  }
  if (bytesRead == 3) {
    String cmd = String((char)buf[0]) + String((char)buf[1]);
    uint8_t intValue = buf[2];
    processCommand(cmd, intValue);
  }
  if (x==1){
    timeClient.update(); 
    time_t epochTime = timeClient.getEpochTime(); 
    struct tm *ptm = gmtime ((time_t *)&epochTime);
    int monthDay = ptm->tm_mday;
    int currentMonth = ptm->tm_mon+1;
    int currentYear = ptm->tm_year+1900;
    String currentDate = String(currentYear) + "-" + String(currentMonth) + "-" + String(monthDay);
    now = millis();
    float humidity= dht.readHumidity();
    float temp = dht.readTemperature();
    int elapsedTime = now - lastPrintTime; 

    if (elapsedTime >= 1000) { 
      lastPrintTime = now;   
      
      tempSamples[sampleCount] = temp;
      humiditySamples[sampleCount] = humidity;
      motionSamples[sampleCount] = detetado;
      lightSamples[sampleCount] = luminosidade;
      sampleCount++;
      Serial.println("Temp: " + String(temp) + ", Humidity: " + String(humidity) + ", Motion: " + String(detetado) + ", Light: " + String(luminosidade));
      if (sampleCount >= intervalo_seg) {
        float tempAverage = 0;
        float humidityAverage = 0;
        float motionAverage = 0;
        float lightAverage = 0;
        for (int i = 0; i < intervalo_seg; i++) {
          tempAverage += tempSamples[i];
          humidityAverage += humiditySamples[i];
          motionAverage += motionSamples[i];
          lightAverage += lightSamples[i];
        }
        tempAverage /= intervalo_seg;
        humidityAverage /= intervalo_seg;
        motionAverage /= intervalo_seg;
        lightAverage /= intervalo_seg;
        sampleCount = 0;

        if(tempAverage >= 20){
            digitalWrite(COOLER_PIN, HIGH); // turn on COOLER
        }else{
           digitalWrite(COOLER_PIN, LOW); // turn off COOLER
        }
        int analogValue = analogRead(LIGHT_SENSOR_PIN); // read the value on analog pin
        lightAverage = map(analogValue, 0, 1023, 155, 0); //converte o sinal analógico em PWM
        if (analogValue < ANALOG_THRESHOLD){
          analogWrite(LED_PIN, lightAverage); //liga o led de acordo com o valor do PWM recebido
        }else{
          analogWrite(LED_PIN, 0); 
        }

        // Update timestamp
        timeClient.update(); 
        epochTime = timeClient.getEpochTime();
        ptm = gmtime ((time_t *)&epochTime);
        monthDay = ptm->tm_mday;
        currentMonth = ptm->tm_mon+1;
        currentYear = ptm->tm_year+1900;
        currentDate = String(currentYear) + "-" + String(currentMonth) + "-" + String(monthDay);
        String dateTime = currentDate +timeClient.getFormattedTime();
        Serial.println(String(idarduino) +String( dateTime)+ "Temperatura"+String(temp) + ",Humididade: " + String(humidityAverage) + ",Movimento: " + String(motionAverage) + ", Luminosidade " + String(lightAverage));

        String message = idarduino + " " +String(currentDate)+"  "+String(timeClient.getFormattedTime())+ " " + "Temperatura"+ " " +String(tempAverage) +" "+"Humidade"+" "+ String(humidityAverage) + " " + "Movimento"+" "+String(detetado) + " "+ "Luminusidade"+" " + String(luminosidade);

        client.println(message);
      }
    }
  }
}
