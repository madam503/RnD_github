#define INTERVAL 10000
#define TX510_RX 10
#define TX510_TX 11

#include <SoftwareSerial.h>

SoftwareSerial TX510Serial(TX510_RX, TX510_TX); 
String command;

void commandIn() {
  if(Serial.available()) {
    command=Serial.readStringUntil('\n');
    Serial.println(command);
    if(command == "등록"){
      Serial.println("Register Face Id start");
      RegisterId();
    }
    else if(command == "인식"){
      Serial.println("Face recognition start");
      FaceRecognition();
    }
    else if(command == "on"){
      Serial.println("display on");
      DisplayOn();
    }
    else if(command == "off"){
      Serial.println("display off");
      DisplayOff();
    }
  }
}

int RegisterId(){

  byte cmd[8] = {0xEF, 0xAA, 0x13, 0x00, 0x00, 0x00, 0x00, 0x13};
  byte response[12];

  TX510Serial.write(cmd, 8);
  delay(500);

  while (TX510Serial.available() > 0 && (unsigned char)TX510Serial.peek() != 0xFF){
    TX510Serial.read();
  }

  memset(response, 0, 12);
  int bytesRead = TX510Serial.readBytes(response, 12);

  Serial.print("Received bytes (");
  Serial.print(bytesRead);
  Serial.println("):");
  for (int i = 0; i < bytesRead; i++) {
    Serial.print(response[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  if (response[8] != 0x00) {
    Serial.println("Invalid egister Face ID!");
    return -1;
  }

  byte crc = 0;
  for (int i = 2; i < 11; i++){
    crc += response[i];
  }

  if (response[11] == crc) {
    int responseHigh = (int) response[9];
    int responseLow = (int) response[10];
    int response_ID = (256 * responseHigh) + responseLow;
    Serial.print("Registered Face ID: ");
    Serial.println(response_ID);
    return response_ID;
  }
  else{
    Serial.println("CRC error!");
    return -1;
  }
}

int FaceRecognition(){

  byte cmd[8] = {0xEF, 0xAA, 0x12, 0x00, 0x00, 0x00, 0x00, 0x12};
  byte response[12];

  TX510Serial.write(cmd, 8);
  delay(500);

  while (TX510Serial.available() > 0 && (unsigned char)TX510Serial.peek() != 0xFF){
    TX510Serial.read();
  }

  memset(response, 0, 12);
  TX510Serial.readBytes(response, 12);

  if (response[8] != 0x00) {
    Serial.println("Invalid Face recognition!");
    return -1;
  }

  byte crc = 0;
  for (int i = 2; i < 11; i++){
    crc += response[i];
  }

  if (response[11] == crc) {
    int responseHigh = (int) response[9];
    int responseLow = (int) response[10];
    int response_ID = (256 * responseHigh) + responseLow;
    return response_ID;
  }
  else{
    Serial.println("CRC error!");
    return -1;
  }
}

int DisplayOn(){

  byte cmd[9] = {0xEF, 0xAA, 0xC1, 0x00, 0x00, 0x00, 0x01, 0x01, 0xC3};
  byte response[10];

  TX510Serial.write(cmd, 9);
  delay(500);

  while (TX510Serial.available() > 0 && (unsigned char)TX510Serial.peek() != 0xFF){
    TX510Serial.read();
  }

  memset(response, 0, 10);
  TX510Serial.readBytes(response, 10);

  if (response[8] != 0x00) {
    Serial.println("Invalid Display On!");
    return -1;
  }
}

int DisplayOff(){

  byte cmd[9] = {0xEF, 0xAA, 0xC1, 0x00, 0x00, 0x00, 0x01, 0x00, 0xC2};
  byte response[10];

  TX510Serial.write(cmd, 9);
  delay(500);

  while (TX510Serial.available() > 0 && (unsigned char)TX510Serial.peek() != 0xFF){
    TX510Serial.read();
  }

  memset(response, 0, 10);
  TX510Serial.readBytes(response, 10);

  if (response[8] != 0x00) {
    Serial.println("Invalid Display Off!");
    return -1;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Setup started");
  Serial.println("사용가능한 명령어는 등록, 인식, on, off 4가지 입니다.");
  TX510Serial.begin(115200);
}

void loop(){
  commandIn();
}