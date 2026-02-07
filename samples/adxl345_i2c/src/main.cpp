#include <Wire.h>

static const uint8_t QMC_ADDR = 0x0D;

// レジスタ
static const uint8_t REG_X_LSB   = 0x00; // 0x00..0x05: X/Y/Z (LSB,MSB) :contentReference[oaicite:3]{index=3}
static const uint8_t REG_STATUS  = 0x06; // DRDYなど :contentReference[oaicite:4]{index=4}
static const uint8_t REG_CTRL1   = 0x09; // OSR/RNG/ODR/MODE :contentReference[oaicite:5]{index=5}
static const uint8_t REG_CTRL2   = 0x0A; // SOFT_RSTなど :contentReference[oaicite:6]{index=6}
static const uint8_t REG_PERIOD  = 0x0B; // Set/Reset period :contentReference[oaicite:7]{index=7}

static void writeReg(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(QMC_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static void readBytes(uint8_t reg, uint8_t* buf, uint8_t len) {
  Wire.beginTransmission(QMC_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false); // repeated start
  Wire.requestFrom(QMC_ADDR, len);
  for (uint8_t i = 0; i < len && Wire.available(); i++) {
    buf[i] = Wire.read();
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  // (任意) ソフトリセットしたいなら：
  // writeReg(REG_CTRL2, 0x80); delay(10);  // SOFT_RST(bit7) :contentReference[oaicite:8]{index=8}

  // 推奨: Set/Reset period = 0x01 :contentReference[oaicite:9]{index=9}
  writeReg(REG_PERIOD, 0x01);

  // CTRL1 = 0x1D:
  // OSR=512(00), RNG=8G(01), ODR=200Hz(11), MODE=Continuous(01) :contentReference[oaicite:10]{index=10}
  writeReg(REG_CTRL1, 0x1D);
}

void loop() {
  // DRDYを見たい場合（必須ではない）：bit0がDRDY :contentReference[oaicite:11]{index=11}
  uint8_t st = 0x00;
  readBytes(REG_STATUS, &st, 1);
  if ((st & 0x01) == 0) { // DRDY=0
    delay(5);
    return;
  }

  uint8_t b[6] = {0};
  readBytes(REG_X_LSB, b, 6);

  int16_t x = (int16_t)((b[1] << 8) | b[0]);
  int16_t y = (int16_t)((b[3] << 8) | b[2]);
  int16_t z = (int16_t)((b[5] << 8) | b[4]);

  Serial.print("x="); Serial.print(x);
  Serial.print(" y="); Serial.print(y);
  Serial.print(" z="); Serial.println(z);

  delay(50);
}
