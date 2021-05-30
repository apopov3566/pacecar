#include <Servo.h>
#include "modes.h"

// START_CODE
modes mode;
unsigned long heartbeat_time;
unsigned long previous_time;
long delta_time;

volatile unsigned long count;
unsigned long previous_count = 0;
long delta_count;

volatile unsigned long last_click = 0;

double prop = 0;
double integral = 0;

int steer_neutral;
int throttle_neutral;

double throttle_pos;
double sc_throttle_pos = 0;
double steering_pos;
double camera_pos;

double speed_pos = 0;
double dist = 0;

byte buffer[2];
commands buffer_cmd;
byte buffer_val;
bool buffer_rev;

long last_move_time;

Servo steer_servo;
Servo throttle_servo;
Servo camera_servo;

size_t comm;

void setModeColor(enum modes m) {
  //analogWrite(9, mode_colors[m][0]);
  //analogWrite(10, mode_colors[m][1]);
  //analogWrite(11, mode_colors[m][2]);

  // Serial.print("mode set to: ");
  // Serial.println(m);
}

bool checkBuffer() {
  return (buffer[0] >> 5) == 0b101; // better system to be added later
}

void parseBuffer() {
  buffer_val = buffer[1];
  buffer_cmd = (commands) (buffer[0] & 0b1111);
  buffer_rev = (buffer[0] >> 4) & 0b1;
}

void executeMessage() {
  switch(buffer_cmd) {
    case STATUS:
      // Serial.println("status");
      break;
    case HEARTBEAT:
      // Serial.println("HEARTBEAT");
      heartbeat_time = millis();
      break;
    case MODE:
      // Serial.println(buffer[1]);
      mode = (modes) buffer[1];
      setModeColor(mode);
      steering_pos = 0;
      throttle_pos = 0;
      // camera_pos = 0;
      speed_pos = 0;
      sc_throttle_pos = 0;
      dist = 0;
      break;
    case SET_STEER:
      // Serial.println(buffer[1]);
      steering_pos = ((double) buffer[1]) / 255.0;
      if (buffer_rev) steering_pos = steering_pos * -1;
      break;
    case SET_THROTTLE:
      // Serial.println(buffer[1]);
      throttle_pos = ((double) buffer[1]) / 255.0;
      if (buffer_rev) throttle_pos = throttle_pos * -1;
      sc_throttle_pos = 0;
      break;
   case SET_CAMERA:
      // Serial.println(buffer[1]);
      camera_pos = ((double) buffer[1]) / 255.0;
      if (buffer_rev) camera_pos = camera_pos * -1;
      break;
   case SET_SPEED:
      speed_pos = ((double) buffer[1]) / 255.0 * MAX_SPEED;
      if (buffer_rev) speed_pos = speed_pos * -1;

      integral = 0;
      prop = 0;
      break;
   case SET_DIST:
      dist = (((double) buffer[1]) / 255.0 * MAX_DIST);
      last_move_time = millis();
      break;
  }
}

void rotate() {
   if(micros() - last_click > 1000) {
    count++;
  }
  last_click = micros();
}

void setup()  {
  Serial.begin(115200);

  throttle_servo.attach(11);
  steer_servo.attach(5);
  camera_servo.attach(6);

  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);

  pinMode(3, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(3), rotate, FALLING);

//  heartbeat_time = millis();
  previous_time = millis();
  last_move_time = millis();
  mode = PASSTHROUGH;
  setModeColor(mode);
}

void loop() {
//  if (mode != LOST && MAX_HEARTBEAT_INTERVAL != 0 && (millis() - heartbeat_time > MAX_HEARTBEAT_INTERVAL)) {
//    Serial.println("HEARTBEAT LOST");
//    mode = LOST; 
//  }

  delta_time = millis() - previous_time;
  delta_count = count - previous_count;

  if(delta_time > MEASURE_INTERVAL) {
    previous_time = millis();
    previous_count = count;

    dist = max(dist - delta_count, 0);
    if(millis() - last_move_time > MAX_MOVE_TIME) {
      dist = 0;
    }
    if(dist == 0) {
      sc_throttle_pos = 0;
    } else {
      double s = (double)delta_count / (double)delta_time * 1000 * (speed_pos < 0 ? -1 : 1);
      prop = speed_pos - s;
      integral = (prop * INTEGRAL_DECAY_PROP) + (integral * (1 - INTEGRAL_DECAY_PROP));
      sc_throttle_pos = C_PROP * prop + C_INTEGRAL * integral;

      if (speed_pos >= 0) {
        sc_throttle_pos = min(sc_throttle_pos, SC_MAX_THROTTLE);
        sc_throttle_pos = max(sc_throttle_pos, 0);
      } else {
        sc_throttle_pos = min(sc_throttle_pos, 0);
        sc_throttle_pos = max(sc_throttle_pos, SC_MIN_THROTTLE);
      }
    }
  }

  if (Serial.available() > 0) {
    comm = Serial.readBytes(buffer, 2);
    
    if (comm == 2 && checkBuffer()) {
      parseBuffer();
      executeMessage();
    }
  }

  if (mode == COMPUTER || mode == COMPUTER_SC) {
    steer_servo.write((steering_pos * steer_prop * STEER_WIDTH) + STEER_CENTER);
    camera_servo.write((camera_pos * CAMERA_WIDTH) + CAMERA_CENTER);
    throttle_servo.write((((mode == COMPUTER_SC) ? sc_throttle_pos : throttle_pos) 
      * THROTTLE_WIDTH) + THROTTLE_CENTER);
  } else {
    steer_servo.write(STEER_CENTER);
    throttle_servo.write(THROTTLE_CENTER);
    camera_servo.write(CAMERA_CENTER);
  }
}
