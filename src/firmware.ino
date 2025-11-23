#include <Arduino.h>
#include <stdint.h>

#ifndef LED_BUILTIN
  #define LED_BUILTIN PC13
#endif

#define LED_PASS PA0
#define LED_FAIL PA1

uint8_t LEDS_BAR[] = {PB1, PB0, PA7, PA6, PA5, PA4, PA3, PA2};

#define IN_PULLUP_PIN PB12
#define IN_DATA_PIN PB13
#define IN_CLK_PIN PB14
#define IN_EN_PIN PB15
#define IN_LD_PIN PA8

#define OUT_CLR_PIN PB9
#define OUT_CLK_PIN PB8
#define OUT_LD_PIN PB7
#define OUT_EN_PIN PB6
#define OUT_DATA_PIN PB4

#define CLK_DELAY 1

void ledOn(uint8_t led) {
  digitalWrite(led, LOW);
}

void ledOff(uint8_t led) {
  digitalWrite(led, HIGH);
}

void bar(uint8_t value) {
  for(uint8_t i = 0; i < 8; i++) {
    if((value & (1<<i)) > 0) {
      ledOn(LEDS_BAR[i]);
    } else {
      ledOff(LEDS_BAR[i]);
    }
  }
}

uint32_t shiftDataIn() {
  return 0;
}

void pullUp() {
  digitalWrite(IN_PULLUP_PIN, HIGH);
}

void pullDown() {
  digitalWrite(IN_PULLUP_PIN, LOW);
}

void disableOut() {
  digitalWrite(OUT_EN_PIN, HIGH);
}

void enableOut() {
  digitalWrite(OUT_EN_PIN, LOW);
}

void pulseClk(uint8_t pin) {
  digitalWrite(pin, HIGH);
  delay(CLK_DELAY);
  digitalWrite(pin, LOW);
  delay(CLK_DELAY);
}

void clearOut() {
  digitalWrite(OUT_CLR_PIN, LOW);
  pulseClk(OUT_CLK_PIN);
  digitalWrite(OUT_CLR_PIN, HIGH);
  pulseClk(OUT_LD_PIN);
}

void shiftDataOut(uint32_t data) {
  for(uint8_t i = 0; i < 32; i++) {
    if ((data & (1 << i)) == 0) {
      digitalWrite(OUT_DATA_PIN, LOW);
    } else {
      digitalWrite(OUT_DATA_PIN, HIGH);
    }

    pulseClk(OUT_CLK_PIN);
  }

  digitalWrite(OUT_DATA_PIN, LOW);

  pulseClk(OUT_LD_PIN);
  pulseClk(OUT_LD_PIN);
  enableOut();
}

void setup() {
  Serial.begin(9600);

  pinMode(LED_BUILTIN, OUTPUT);
  ledOff(LED_BUILTIN);

  pinMode(LED_PASS, OUTPUT);
  pinMode(LED_FAIL, OUTPUT);
  ledOff(LED_PASS);
  ledOff(LED_FAIL);

  for(uint8_t i = 0; i < 8; i++) {
    pinMode(LEDS_BAR[i], OUTPUT);
    ledOff(LEDS_BAR[i]);
  }

  pinMode(IN_PULLUP_PIN, OUTPUT);
  pullDown();
  pinMode(IN_DATA_PIN, INPUT);
  pinMode(IN_CLK_PIN, OUTPUT);
  pinMode(IN_EN_PIN, OUTPUT);
  pinMode(IN_LD_PIN, OUTPUT);
  shiftDataIn();

  pinMode(OUT_DATA_PIN, OUTPUT);
  digitalWrite(OUT_DATA_PIN, LOW);
  pinMode(OUT_CLK_PIN, OUTPUT);
  digitalWrite(OUT_CLK_PIN, LOW);
  pinMode(OUT_EN_PIN, OUTPUT);
  digitalWrite(OUT_EN_PIN, HIGH);
  pinMode(OUT_LD_PIN, OUTPUT);
  digitalWrite(OUT_LD_PIN, LOW);
  pinMode(OUT_CLR_PIN, OUTPUT);
  digitalWrite(OUT_CLR_PIN, HIGH);
  clearOut();
  disableOut();
}

uint8_t value = 0;

void loop() {

  ledOn(LED_BUILTIN);
  Serial.println("Hello world hehe!");
  bar((1<<(value%9))-1);

  if (value % 2) {
    ledOn(LED_PASS);
    ledOff(LED_FAIL);
    shiftDataOut(0xFF00FF00);
  } else {
    ledOff(LED_PASS);
    ledOn(LED_FAIL);
    shiftDataOut(0x55555555);
  }

  delay(200);

  ledOff(LED_BUILTIN);
  delay(800);
  value++;
}
