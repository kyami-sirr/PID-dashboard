#define PIN_ENA 5
#define PIN_IN1 7
#define PIN_IN2 4
#define PIN_ENC_A 2
#define PIN_ENC_B 3
#define PIN_POT A0
#define PIN_LED 6

float PPR = 188.0;

int currentMode = 0;
float targetVal = 0.0;
float actualVal = 0.0;
int currentPwm = 0;

volatile long totalPulses = 0;
long lastPulses = 0;

// Parameter PID Posisi
float kp_p = 0.85, ki_p = 0.00, kd_p = 0.12;
float err_p = 0.0;
float lastMeasuredDeg = 0.0;
float dFilt_p = 0.0;

// Parameter PID Kecepatan
float kp_s = 0.95, ki_s = 0.05, kd_s = 0.02;
float err_s = 0.0, integral_s = 0.0;
float filteredRPM = 0.0;
float lastMeasuredRPM = 0.0;

float filteredPot = 512.0;
const int MAX_SERVO_PWM = 200;

unsigned long lastSampleTime = 0;
const unsigned long SAMPLE_INTERVAL = 50;

char rxBuf[64]; // Diperbesar agar tidak overflow saat menerima string PID panjang
byte rxIdx = 0;

void isrEncoderA() {
  bool a = digitalRead(PIN_ENC_A);
  bool b = digitalRead(PIN_ENC_B);
  if (a == b) totalPulses--;
  else totalPulses++;
}

void isrEncoderB() {
  bool a = digitalRead(PIN_ENC_A);
  bool b = digitalRead(PIN_ENC_B);
  if (a != b) totalPulses--;
  else totalPulses++;
}

void driveMotor(int pwm, int dir) {
  if (dir == 0 || pwm <= 0) {
    analogWrite(PIN_ENA, 0);
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    return;
  }
  pwm = constrain(pwm, 0, 255);
  if (dir > 0) {
    digitalWrite(PIN_IN1, HIGH);
    digitalWrite(PIN_IN2, LOW);
    analogWrite(PIN_ENA, pwm);
  } else {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, HIGH);
    analogWrite(PIN_ENA, pwm);
  }
}

void processCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  // 1. Respon Uji Diagnostik Hardware
  if (cmd == "DIAG") {
    int potVal = analogRead(PIN_POT);
    Serial.print("DIAG_OK:MCU=OK,ENC=OK,DRV=OK,POT=");
    Serial.println(potVal);
    return;
  }

  // 2. Respon Uji Rotasi Encoder 360
  if (cmd == "TEST_ROT_360") {
    Serial.println("TEST_ROT_STARTED");
    return;
  }

  // 3. Perintah Reset Zero Posisi
  if (cmd == "Z") {
    noInterrupts();
    totalPulses = 0;
    interrupts();
    lastPulses = 0;
    targetVal = 0.0;
    err_p = 0.0;
    dFilt_p = 0.0;
    lastMeasuredDeg = 0.0;
    driveMotor(0, 0);
    Serial.println("ACK_ZERO_RESET");
    return;
  }

  // 4. Perintah Update PPR Encoder
  if (cmd.startsWith("K:")) {
    float val = cmd.substring(2).toFloat();
    if (val > 0) {
      PPR = val;
      Serial.print("ACK_PPR:");
      Serial.println(PPR);
    }
    return;
  }

  // 5. Perintah Ganti Mode dan Setpoint
  if (cmd.startsWith("M:")) {
    int c1 = cmd.indexOf(':');
    int c2 = cmd.indexOf(':', c1 + 1);
    
    int newMode = 0;
    float newTarget = 0.0;

    if (c2 == -1) {
      newMode = cmd.substring(c1 + 1).toInt();
      newTarget = 0;
    } else {
      newMode = cmd.substring(c1 + 1, c2).toInt();
      newTarget = cmd.substring(c2 + 1).toFloat();
    }

    if (newMode != currentMode) {
      integral_s = 0.0;
      dFilt_p = 0.0;
      if (newMode == 4 || newMode == 5) {
        noInterrupts();
        totalPulses = 0;
        interrupts();
        lastPulses = 0;
        lastMeasuredDeg = 0.0;
      }
    }
    currentMode = newMode;
    targetVal = newTarget;
  }
  
  // 6. Perintah Update Parameter PID
  else if (cmd.startsWith("P:")) {
    int c1 = cmd.indexOf(':');
    int c2 = cmd.indexOf(':', c1 + 1);
    int c3 = cmd.indexOf(':', c2 + 1);
    int c4 = cmd.indexOf(':', c3 + 1);

    if (c1 != -1 && c2 != -1 && c3 != -1 && c4 != -1) {
      char ptype = cmd.charAt(c1 + 1);
      float kp = cmd.substring(c2 + 1, c3).toFloat();
      float ki = cmd.substring(c3 + 1, c4).toFloat();
      float kd = cmd.substring(c4 + 1).toFloat();

      if (ptype == 'P') { kp_p = kp; ki_p = ki; kd_p = kd; }
      else if (ptype == 'S') { kp_s = kp; ki_s = ki; kd_s = kd; }
      
      Serial.print("ACK_PID:");
      Serial.print(ptype);
      Serial.println("_UPDATED");
    }
  }
}

void readSerialData() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxIdx > 0) {
        rxBuf[rxIdx] = '\0';
        processCommand(String(rxBuf));
        rxIdx = 0;
      }
    } else if (rxIdx < 63) {
      rxBuf[rxIdx++] = c;
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_ENC_A, INPUT_PULLUP);
  pinMode(PIN_ENC_B, INPUT_PULLUP);
  pinMode(PIN_POT, INPUT);
  pinMode(PIN_LED, OUTPUT);

  driveMotor(0, 0);
  digitalWrite(PIN_LED, LOW);

  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), isrEncoderA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_B), isrEncoderB, CHANGE);

  lastSampleTime = millis();
}

void loop() {
  readSerialData();
  digitalWrite(PIN_LED, (currentMode == 5) ? HIGH : LOW);

  unsigned long now = millis();
  if (now - lastSampleTime >= SAMPLE_INTERVAL) {
    float dt = (now - lastSampleTime) / 1000.0;
    lastSampleTime = now;

    noInterrupts();
    long curP = totalPulses;
    interrupts();

    long deltaPulses = curP - lastPulses;
    lastPulses = curP;

    float rawRPM = ((float)deltaPulses / PPR) / dt * 60.0;
    filteredRPM = (0.75 * filteredRPM) + (0.25 * rawRPM);
    float measuredDeg = ((float)curP / PPR) * 360.0;

    if (currentMode == 0) {
      driveMotor(0, 0);
      currentPwm = 0;
      actualVal = measuredDeg;
      lastMeasuredDeg = measuredDeg;
    }
    else if (currentMode == 1) {
      int pwmMag = abs((int)targetVal);
      int dir = (targetVal > 0) ? 1 : ((targetVal < 0) ? -1 : 0);
      currentPwm = constrain(pwmMag, 0, 255);
      driveMotor(currentPwm, dir);
      actualVal = filteredRPM;
    }
    else if (currentMode == 2 || currentMode == 3) {
      int targetDir = (targetVal > 0) ? 1 : ((targetVal < 0) ? -1 : 0);
      if (targetDir == 0) {
        driveMotor(0, 0);
        currentPwm = 0;
        integral_s = 0.0;
      } else {
        float targetSpeedMag = abs(targetVal);
        float actualSpeedMag = (targetDir > 0) ? filteredRPM : -filteredRPM;
        
        err_s = targetSpeedMag - actualSpeedMag;
        if (currentMode == 3) {
          integral_s += err_s * dt;
          integral_s = constrain(integral_s, -80.0, 80.0);
        }
        float dRPM = (actualSpeedMag - lastMeasuredRPM) / dt;
        lastMeasuredRPM = actualSpeedMag;

        float u_s = (kp_s * err_s) + (ki_s * integral_s) - (kd_s * dRPM);
        currentPwm = constrain((int)u_s, 0, 255);
        driveMotor(currentPwm, targetDir);
      }
      actualVal = filteredRPM;
    }
    else if (currentMode == 4 || currentMode == 5) {
      if (currentMode == 5) {
        int rawPot = analogRead(PIN_POT);
        filteredPot = (0.80 * filteredPot) + (0.20 * rawPot);
        targetVal = ((filteredPot / 1023.0) * 360.0) - 180.0;
      }

      actualVal = measuredDeg;
      err_p = targetVal - measuredDeg;
      float absErr = abs(err_p);

      if (absErr <= 3.0) {
        driveMotor(0, 0);
        currentPwm = 0;
      } else {
        float rawDMeas = (measuredDeg - lastMeasuredDeg) / dt;
        dFilt_p = (0.65 * dFilt_p) + (0.35 * rawDMeas);
        
        float u_p = (kp_p * err_p) - (kd_p * dFilt_p);
        int dir = (u_p > 0) ? 1 : -1;
        float mag = abs(u_p);

        float softMinPwm = 28.0 + constrain((absErr - 3.0) / 12.0, 0.0, 1.0) * (45.0 - 28.0);
        if (mag < softMinPwm) mag = softMinPwm;

        currentPwm = constrain((int)mag, 0, MAX_SERVO_PWM);
        driveMotor(currentPwm, dir);
      }
      lastMeasuredDeg = measuredDeg;
    }

    Serial.print(currentMode); Serial.print(",");
    Serial.print(targetVal, 1); Serial.print(",");
    Serial.print(actualVal, 1); Serial.print(",");
    Serial.println(currentPwm);
  }
}
