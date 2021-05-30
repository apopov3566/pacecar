enum commands{STATUS, HEARTBEAT, MODE, SET_STEER, SET_THROTTLE, SET_CAMERA, SET_SPEED, SET_DIST};
enum modes{PASSTHROUGH, COMPUTER, COMPUTER_SC, LOST};

const double WIDTH = 500;

const int STEER_CENTER = 92;
const double STEER_WIDTH = 45;
double steer_prop = 1.0;

const int THROTTLE_CENTER = 90;
const double THROTTLE_WIDTH = 45;

const int CAMERA_CENTER = 90;
const double CAMERA_WIDTH = 90;

const double MAX_DIST = 300;
const double MAX_SPEED = 20;
const int MAX_MOVE_TIME = 10000;

const double MEASURE_INTERVAL = 5;
const double INTEGRAL_DECAY_PROP = 0.01;
const double C_PROP = 0.02;
const double C_INTEGRAL = 0.01;

const double SC_MAX_THROTTLE = 0.4;
const double SC_MIN_THROTTLE = -0.4;

const int mode_colors[3][3] = {{100,0,0},{0,100,0},{0,0,100}};

const unsigned long MAX_HEARTBEAT_INTERVAL = 0;
