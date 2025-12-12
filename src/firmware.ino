#include <Arduino.h>
#include <stdint.h>

#ifndef LED_BUILTIN
  #define LED_BUILTIN PC13
#endif

#define LED_PASS PA0
#define LED_FAIL PA1

uint8_t LEDS_BAR[] = {PA2, PA3, PA4, PA5, PA6, PA7, PB0, PB1};

#define IN_PULLUP_PIN PB13
#define IN_DATA_PIN PB14
#define IN_EN_PIN PB15
#define IN_LD_PIN PA9
#define IN_CLK_PIN PA8

#define OUT_CLR_PIN PB9
#define OUT_CLK_PIN PB8
#define OUT_LD_PIN PB7
#define OUT_EN_PIN PB6
#define OUT_DATA_PIN PB4

#define CLK_DELAY 0
#define LD_DELAY 1
#define CMD_TIMEOUT 200

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

void disableIn() {
  digitalWrite(IN_EN_PIN, HIGH);
}

void enableIn() {
  digitalWrite(IN_EN_PIN, LOW);
}

void pulseClk(uint8_t pin) {
  digitalWrite(pin, HIGH);
  if(CLK_DELAY != 0) delayMicroseconds(CLK_DELAY);
  digitalWrite(pin, LOW);
  if(CLK_DELAY != 0) delayMicroseconds(CLK_DELAY);
}

uint32_t shiftDataIn() {
  uint32_t value = 0;

  disableIn();

  digitalWrite(IN_LD_PIN, LOW);
  delayMicroseconds(LD_DELAY);
  digitalWrite(IN_LD_PIN, HIGH);
  delayMicroseconds(LD_DELAY);

  enableIn();

  for(uint8_t i = 0; i < 32; i++) {
    if (digitalRead(IN_DATA_PIN) == HIGH) {
      value = value | (((uint32_t)0x1) << i);
    }

    pulseClk(IN_CLK_PIN);
  }

  return value;
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

void clearOut() {
  digitalWrite(OUT_CLR_PIN, LOW);
  pulseClk(OUT_CLK_PIN);
  digitalWrite(OUT_CLR_PIN, HIGH);
  pulseClk(OUT_LD_PIN);
}

void shiftDataOut(uint32_t data) {
  for(int8_t i = 31; i >= 0; i--) {
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
  Serial.begin(576000);

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
  digitalWrite(IN_CLK_PIN, LOW);
  pinMode(IN_EN_PIN, OUTPUT);
  digitalWrite(IN_EN_PIN, LOW);
  pinMode(IN_LD_PIN, OUTPUT);
  digitalWrite(IN_LD_PIN, HIGH);
  disableIn();

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

void loop() {
  if (Serial.available() > 0) {
    ledOn(LED_BUILTIN);

    char cmd = Serial.read();
    Serial.setTimeout(CMD_TIMEOUT);

    switch(cmd) {
      case 'r':
      case 'R': {
        setup();
      }
      break;

      case 'i':
      case 'I': {
        pullDown();
        uint32_t down = shiftDataIn();

        pullUp();
        uint32_t up = shiftDataIn();

        char state[33] = {0};
        for(int8_t i = 31; i >= 0; i--) {
          uint32_t u = up & (1 << i);
          uint32_t d = down & (1 << i);

          if (u != d)      state[i] = 'Z';
          else if (u == 0) state[i] = '0';
          else             state[i] = '1';
        }
        Serial.println(state);
      }
      break;

      case 'o':
      case 'O': {
        union {
          char bytes[4];
          uint32_t value;
        } state;

        Serial.readBytes(state.bytes, 4);
        shiftDataOut(state.value);
      }
      break;

      case 'b':
      case 'B': {
        char state[1] = {0};
        Serial.readBytes(state, 1);
        bar(state[0]);
      }
      break;

      case 'p':
      case 'P': {
        char state[1] = {0};
        Serial.readBytes(state, 1);
        if (state[0] == '1') ledOn(LED_PASS);
        else                 ledOff(LED_PASS);
      }
      break;
      case 'f':
      case 'F': {
        char state[1] = {0};
        Serial.readBytes(state, 1);
        if (state[0] == '1') ledOn(LED_FAIL);
        else                 ledOff(LED_FAIL);
      }
      break;

      default:
        // Nothing to do.
        break;
    }
  }
  ledOff(LED_BUILTIN);
}
