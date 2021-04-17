enum commands{STATUS, HEARTBEAT, MODE, SET_STEER, SET_THROTTLE};
enum modes{PASSTHROUGH, COMPUTER, LOST};

const double WIDTH = 500;

const int STEER_CENTER = 92;
const double STEER_WIDTH = 45;
double steer_prop = 1.0;

const int THROTTLE_CENTER = 90;
const double THROTTLE_WIDTH = 45;

const int mode_colors[3][3] = {{100,0,0},{0,100,0},{0,0,100}};

const unsigned long MAX_HEARTBEAT_INTERVAL = 1000;
