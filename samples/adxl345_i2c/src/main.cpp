#include <Wire.h>

static const uint8_t ADXL_ADDR = 0x53; // SDO/ALT LOW:0x53, HIGH:0x1D
static const uint8_t REG_DEVID      = 0x00;
static const uint8_t REG_BW_RATE    = 0x2C;
static const uint8_t REG_POWER_CTL  = 0x2D;
static const uint8_t REG_DATA_FORMAT= 0x31;
static const uint8_t REG_DATAX0     = 0x32;

static void writeReg(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(ADXL_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static uint8_t readReg(uint8_t reg) {
  Wire.beginTransmission(ADXL_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);           // repeated start
  Wire.requestFrom(ADXL_ADDR, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0xFF;
}

static void readMulti(uint8_t reg, uint8_t *buf, size_t len) {
  Wire.beginTransmission(ADXL_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);           // repeated start
  Wire.requestFrom(ADXL_ADDR, (uint8_t)len);
  for (size_t i = 0; i < len && Wire.available(); i++) buf[i] = Wire.read();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  uint8_t id = readReg(REG_DEVID);
  Serial.print("DEVID=0x"); Serial.println(id, HEX);
  if (id != 0xE5) {
    Serial.println("ADXL345 not found (check wiring/address).");
    while (1) delay(1000);
  }

  writeReg(REG_BW_RATE, 0x0A);         // 100 Hz
  writeReg(REG_DATA_FORMAT, 0x08);     // FULL_RES=1, range=+-2g
  writeReg(REG_POWER_CTL, 0x08);       // MEASURE=1
}

void loop() {
  uint8_t b[6] = {0};
  readMulti(REG_DATAX0, b, 6);

  int16_t x = (int16_t)((b[1] << 8) | b[0]);
  int16_t y = (int16_t)((b[3] << 8) | b[2]);
  int16_t z = (int16_t)((b[5] << 8) | b[4]);

  Serial.print("x="); Serial.print(x);
  Serial.print(" y="); Serial.print(y);
  Serial.print(" z="); Serial.println(z);

  delay(50);
}
