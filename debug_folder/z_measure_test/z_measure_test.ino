/*
  2022/07/29（金）記入者：船橋佑｜xyzのキャリブレーション後、z軸の計測のみ行う。その際、計測してからの反映が
 serialだと遅いので、計測時のみ2000pulse/秒ではなく100pulse/秒でおこなう。
  2022/08/01（月）関数化したよ
*/

#include <AccelStepper.h>

//x軸のモーターのピン
#define STEPPER_PULSE_PIN_x 11
#define STEPPER_CCW_PIN_x   10
#define LIMIT_INT0_PIN_x    2
#define LIMIT_INT1_PIN_x    3

//y軸のモーターのピン
#define STEPPER_PULSE_PIN_y 13
#define STEPPER_CCW_PIN_y   12
#define LIMIT_INT0_PIN_y    20
#define LIMIT_INT1_PIN_y    21

//z軸のモーターのピン
#define STEPPER_PULSE_PIN_z 9
#define STEPPER_CCW_PIN_z   8
#define LIMIT_INT0_PIN_z    19
#define LIMIT_INT1_PIN_z    18

#define CARIVSPEED -2000

bool islimit0_x = false;
bool islimit1_x = false;
bool islimit0_y = false;
bool islimit1_y = false;
bool islimit0_z = false;
bool islimit1_z = false;
long move_position;

bool serial_flag1 = false;
bool serial_flag2 = false;

//x軸のステッパー変数
AccelStepper stepper_x(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_x, STEPPER_CCW_PIN_x
);

//y軸のステッパー変数
AccelStepper stepper_y(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_y, STEPPER_CCW_PIN_y
);

//z軸のステッパー変数
AccelStepper stepper_z(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_z, STEPPER_CCW_PIN_z
);


void flag_0() {
  //  Serial.println("limit0!!!");
  islimit0_x = true;
}

void flag_1() {
  //  Serial.println("limit1!!!");
  islimit1_x = true;
}

void flag_2() {
  //  Serial.println("limit0!!!");
  islimit0_y = true;
}

void flag_3() {
  //  Serial.println("limit1!!!");
  islimit1_y = true;
}

void flag_4() {
  //  Serial.println("limit0!!!");
  islimit0_z = true;
}

void flag_5() {
  //  Serial.println("limit1!!!");
  islimit1_z = true;
}

void stop_check() {
  if (Serial.available()) {
    String line2 = Serial.readStringUntil(';');
    if (line2.equals("stop")) {
      stepper_x.stop();
      stepper_y.stop();
      stepper_z.stop();
      Serial.println("move_z_end");
    }
  }
}

void run_speed(AccelStepper z){
  while (true) { //モーターが端っこに来るまで動く
    z.runSpeed();
    stop_check();
    Serial.print(islimit0_x);
    Serial.print(islimit1_x);
    Serial.print(islimit0_y);
    Serial.print(islimit1_y);
    Serial.print(islimit0_z);
    Serial.println(islimit1_z);
    if (islimit0_x==true|islimit1_x==true|islimit0_y==true|islimit1_y==true|islimit0_z==true|islimit1_z==true) {
      Serial.println("fogefoge2");
      break;
    }
  }
  z.stop(); //端まで来たら止まる
  z.setCurrentPosition(0); //0ポジ設定
  islimit0_x =false;
  islimit1_x =false;
  islimit0_y =false;
  islimit1_y =false;
  islimit0_z =false;
  islimit1_z =false;
  Serial.println("fogefoge3");
}  


void move_to(AccelStepper x,int y,int z){
  x.moveTo(y);
  x.setSpeed(z);
  Serial.print(islimit0_x);
  Serial.print(islimit1_x);
  Serial.print(islimit0_y);
  Serial.print(islimit1_y);
  Serial.print(islimit0_z);
  Serial.println(islimit1_z);
  while (true) {
    x.runSpeedToPosition();
    stop_check();
    if (x.currentPosition() == y) {
      break;
    }
  }
  islimit0_x =false;
  islimit1_x =false;
  islimit0_y =false;
  islimit1_y =false;
  islimit0_z =false;
  islimit1_z =false;
}  


void setup() {
  // Configure GPIO Pins
  pinMode(STEPPER_PULSE_PIN_x, OUTPUT);
  pinMode(STEPPER_CCW_PIN_x,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_x, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_x, INPUT_PULLUP);
  pinMode(STEPPER_PULSE_PIN_y, OUTPUT);
  pinMode(STEPPER_CCW_PIN_y,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_y, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_y, INPUT_PULLUP);
  pinMode(STEPPER_PULSE_PIN_z, OUTPUT);
  pinMode(STEPPER_CCW_PIN_z,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_z, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_z, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_x), flag_0, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_x), flag_1, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_y), flag_2, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_y), flag_3, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_z), flag_4, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_z), flag_5, RISING);

  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor
  stepper_x.setMaxSpeed(2000);  // 脱調防止
  stepper_x.setSpeed(CARIVSPEED);
  stepper_y.setMaxSpeed(2000);  // 脱調防止
  stepper_y.setSpeed(-2000);
  stepper_z.setMaxSpeed(2000);  // 脱調防止
  stepper_z.setSpeed(CARIVSPEED);

  while (true) {
    if (Serial.available()) {
      String line = Serial.readStringUntil(';');
      if (line.equals("up_Z")) {
        serial_flag1 = true;
      }else if(line.equals("cariv_start")){
        serial_flag2 = true;
      }
    }

    if(serial_flag1){
      run_speed(stepper_z);
      delay(1000);     
      serial_flag1 = false;
      Serial.println("Z_end");
      break;
    }else if(serial_flag2){
      run_speed(stepper_z);
      delay(1000);  
      run_speed(stepper_x);
      delay(1000);
      move_to(stepper_x, 25000, 2000);
      delay(1000);
      Serial.println("foge1");
      run_speed(stepper_y);
      Serial.println("foge2");
      delay(1000);
      move_to(stepper_y, 25000, 2000);
      delay(1000);      
      serial_flag2 = false;
      Serial.println("cariv_end");
      break;
    }
  }
}
      


//z軸を下に動かす。何もしなくてもいずれ止まるが、stop;というシリアル操作により能動的に制御可能
void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil(';');
    if (line.equals("move_z_start")) {
      stepper_z.moveTo(40000);
      stepper_z.setSpeed(100);
      while (true) {
        stepper_z.runSpeedToPosition();
        //        stop_check();
        if (Serial.available()) {
          String line2 = Serial.readStringUntil(';');
          if (line2.equals("stop")) {
            stepper_z.stop();
          } else if (line2.equals("sp-Z")) {
            stepper_z.setSpeed(-2000);
            while (true) { //モーターが端っこに来るまで動く
              stepper_z.runSpeed();
              stop_check();
              if (islimit0_z) {
                Serial.println("move_z_end");
                stepper_z.stop();
              }
            }
          }
        }
      }
    }
  }
}
