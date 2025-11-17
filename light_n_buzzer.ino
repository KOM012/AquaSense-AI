// ARDUINO CODE - FIXED FOR PYTHON TRANSMITTER
const int LED_PIN = 9;
const int BUZZER_PIN = 10;

// Frequencies
const int DROWNING_FREQ = 4000;      // High frequency
const int OBSTRUCTION_FREQ = 1000;   // Low frequency

// Pulsing control
unsigned long lastPulseTime = 0;
const unsigned long PULSE_INTERVAL = 1000;  // 1s on / 1s off
bool pulseState = false;

// Alert states
bool drowningActive = false;
bool obstructionActive = false;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("READY: 0=Off, 1=Drowning, 2=Obstruction");
}

void loop() {

  // HANDLE SERIAL INPUT
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Ignore newline + carriage return
    if (cmd == '\n' || cmd == '\r') return;

    handleCommand(cmd);
  }

  // HANDLE OBSTRUCTION PULSE (ONLY IF ACTIVE)
  if (obstructionActive && !drowningActive) {
    unsigned long currentTime = millis();

    if (currentTime - lastPulseTime >= PULSE_INTERVAL) {
      pulseState = !pulseState;
      lastPulseTime = currentTime;

      if (pulseState) {
        digitalWrite(LED_PIN, HIGH);
        tone(BUZZER_PIN, OBSTRUCTION_FREQ);
        Serial.println("PULSE: Obstruction ON");
      } else {
        digitalWrite(LED_PIN, LOW);
        noTone(BUZZER_PIN);
        Serial.println("PULSE: Obstruction OFF");
      }
    }
  }
}

void handleCommand(char command) {

  // ========== DROWNING ==========  
  if (command == '1') {
    drowningActive = true;
    obstructionActive = false;

    digitalWrite(LED_PIN, HIGH);
    tone(BUZZER_PIN, DROWNING_FREQ);

    Serial.println("ALERT: DROWNING - Continuous high frequency");
  }

  // ========== OBSTRUCTION (PULSING) ==========
  else if (command == '2') {
    drowningActive = false;
    obstructionActive = true;

    pulseState = true;                  // Start ON
    lastPulseTime = millis();           // Reset timer
    digitalWrite(LED_PIN, HIGH);
    tone(BUZZER_PIN, OBSTRUCTION_FREQ);

    Serial.println("ALERT: OBSTRUCTION - Low frequency pulsing");
  }

  // ========== CLEAR EVERYTHING ==========
  else if (command == '0') {
    drowningActive = false;
    obstructionActive = false;

    digitalWrite(LED_PIN, LOW);
    noTone(BUZZER_PIN);

    pulseState = false; // RESET pulse

    Serial.println("CLEAR: All alerts off");
  }

  // ========== UNKNOWN COMMAND ==========
  else {
    Serial.print("UNKNOWN COMMAND: ");
    Serial.println(command);
  }
}