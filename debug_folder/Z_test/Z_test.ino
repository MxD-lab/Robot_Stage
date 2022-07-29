/*
  2022/07/10（月）記入者：船橋佑｜xyzのキャリブレーションを行ったのち、ロードセルの値によって制御するコード作成
*/

#include <AccelStepper.h>



//z軸のモーターのピン
#define STEPPER_PULSE_PIN_z 9
#define STEPPER_CCW_PIN_z   8
#define LIMIT_INT0_PIN_z    19
#define LIMIT_INT1_PIN_z    18

#define CARIVSPEED -2000


bool islimit0_z = false;
bool islimit1_z = false;
long move_position;



//z軸のステッパー変数
AccelStepper stepper_z(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_z, STEPPER_CCW_PIN_z
);




void flag_4() {
  //  Serial.println("limit0!!!");
  islimit0_z = true;
}

void flag_5() {
  //  Serial.println("limit1!!!");
  islimit1_z = true;
}



void setup() {
  // Configure GPIO Pins

  pinMode(STEPPER_PULSE_PIN_z, OUTPUT);
  pinMode(STEPPER_CCW_PIN_z,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_z, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_z, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_z), flag_4, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_z), flag_5, RISING);

  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor

  stepper_z.setMaxSpeed(2000);  // 脱調防止
  //  stepper_z.setSpeed(CARIVSPEED); //なんかうまくいかない
  stepper_z.setSpeed(-1000);

//  stepper_z.setCurrentPosition(0); //0ポジ設定

  //    stepper_z.moveTo(-1000);
  //    stepper_z.setSpeed(-2000);
  //    while (true) {
  //      stepper_z.runSpeedToPosition();
  //      //Serial.println(stepper_z.currentPosition());
  //      if (stepper_z.currentPosition() == -1000) {
  //        break;
  //      }
  //    }
  //  int count = 0;
  while (true) {
    stepper_z.runSpeed();
//    count++;
  }

  //  for (int i = 0; i < 30000; i++) {
  //    Serial.println(i);
  //    stepper_z.runSpeed();
  //    count++;
  //  }
  Serial.println("owa");
//  Serial.println(count);



}


void loop() {
}
