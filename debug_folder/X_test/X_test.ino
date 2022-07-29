/*
  2022/07/10（月）記入者：船橋佑｜xyzのキャリブレーションを行ったのち、ロードセルの値によって制御するコード作成
*/

#include <AccelStepper.h>



//z軸のモーターのピン
#define STEPPER_PULSE_PIN_x 11
#define STEPPER_CCW_PIN_x   10
#define LIMIT_INT0_PIN_x    2
#define LIMIT_INT1_PIN_x    3

#define CARIVSPEED -2000


bool islimit0_x = false;
bool islimit1_x = false;
long move_position;



//x軸のステッパー変数
AccelStepper stepper_x(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_x, STEPPER_CCW_PIN_x
);




void flag_4() {
  //  Serial.println("limit0!!!");
  islimit0_x = true;
}

void flag_5() {
  //  Serial.println("limit1!!!");
  islimit1_x = true;
}



void setup() {
  // Configure GPIO Pins

  pinMode(STEPPER_PULSE_PIN_x, OUTPUT);
  pinMode(STEPPER_CCW_PIN_x,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_x, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_x, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_x), flag_4, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_x), flag_5, RISING);

  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor

  stepper_x.setMaxSpeed(2000);  // 脱調防止
  //  stepper_x.setSpeed(CARIVSPEED); //なんかうまくいかない
  stepper_x.setSpeed(1000);

  //  stepper_x.setCurrentPosition(0); //0ポジ設定

  //  stepper_x.moveTo(-1000);
  //  stepper_x.setSpeed(-2000);
  //  while (true) {
  //    stepper_x.runSpeedToPosition();
  //    //Serial.println(stepper_x.currentPosition());
  //    if (stepper_x.currentPosition() == -1000) {
  //      break;
  //    }
  //  }
  int count=0;

  while(true){
    stepper_x.runSpeed();
    count++;
  }
  
//  for (int i = 0; i < 30000; i++) {
////    Serial.println(i);
//    stepper_x.runSpeed();
//    count++;
//  }
  Serial.println("owa");
  Serial.println(count);



}


void loop() {
}
