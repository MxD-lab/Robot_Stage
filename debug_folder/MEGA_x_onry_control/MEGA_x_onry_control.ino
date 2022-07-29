/*
2022/06/27（月）記入者：船橋佑｜xのキャリブレーションを行ったのち、自由に制御するコード作成.
*/


#include <AccelStepper.h>

// GPIO Pin Definition
//X軸のみ
#define STEPPER_PULSE_PIN 13
#define STEPPER_CCW_PIN   12
#define LIMIT_INT0_PIN    20
#define LIMIT_INT1_PIN    21

#define STEPPER_PULSE_PIN2 9
#define STEPPER_CCW_PIN2   8
#define LIMIT_INT0_PIN2    19
#define LIMIT_INT1_PIN2    18

#define STEPPER_PULSE_PIN_x 11
#define STEPPER_CCW_PIN_x   10
#define LIMIT_INT0_PIN_x    2
#define LIMIT_INT1_PIN_x    3

#define CARIVSPEED -2000
char key; //手元の停止信号用
bool islimit0 = false;
bool islimit1 = false;
bool islimit2 = false;
bool islimit3 = false;
bool islimitx0 = false;
bool islimitx1 = false;
long move_position;

//x軸のステッパー変数
AccelStepper stepper_x(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN_x, STEPPER_CCW_PIN_x
);

AccelStepper stepper(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN, STEPPER_CCW_PIN
);

AccelStepper stepper2(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN2, STEPPER_CCW_PIN2
);

void flag_0() {
  //  Serial.println("limit0!!!");
  islimit0 = true;
}

void flag_1() {
  //  Serial.println("limit1!!!");
  islimit1 = true;
}

void flag_2() {
  //  Serial.println("limit0!!!");
  islimit2 = true;
}

void flag_3() {
  //  Serial.println("limit1!!!");
  islimit3 = true;
}

void flag_x0() {
  //  Serial.println("limit0!!!");
  islimitx0 = true;
}

void flag_x1() {
  //  Serial.println("limit1!!!");
  islimitx1 = true;
}

void stop_check() {
  if (islimit1) {
    Serial.print("計測が終了しました");
    //    stepper.stop();
    islimit0 = islimit1 = false;
    while (true) {
      stepper.stop();
    }
  } else if (Serial.available()) {
    key = Serial.read();
    if (key == 's') {
      stepper.stop();
      //      stepper2.stop();
      //      stepper3.stop();
      Serial.print("read key = ");
      Serial.println(key);
      Serial.println("stop");
    }
  }

}

void setup() {
  // Configure GPIO Pins
  pinMode(STEPPER_PULSE_PIN, OUTPUT);
  pinMode(STEPPER_CCW_PIN,   OUTPUT);
  pinMode(LIMIT_INT0_PIN, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN, INPUT_PULLUP);
  pinMode(STEPPER_PULSE_PIN2, OUTPUT);
  pinMode(STEPPER_CCW_PIN2,   OUTPUT);
  pinMode(LIMIT_INT0_PIN2, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN2, INPUT_PULLUP);
  pinMode(STEPPER_PULSE_PIN_x, OUTPUT);
  pinMode(STEPPER_CCW_PIN_x,   OUTPUT);
  pinMode(LIMIT_INT0_PIN_x, INPUT_PULLUP);
  pinMode(LIMIT_INT1_PIN_x, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN), flag_0, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN), flag_1, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN2), flag_2, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN2), flag_3, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_x), flag_x0, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_x), flag_x1, RISING);
  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor
  stepper.setMaxSpeed(2000);  // 脱調防止
  stepper.setSpeed(CARIVSPEED);
  stepper2.setMaxSpeed(2000);  // 脱調防止
  stepper2.setSpeed(CARIVSPEED);
  stepper_x.setMaxSpeed(2000);  // 脱調防止
  stepper_x.setSpeed(CARIVSPEED);

  Serial.print("islimit0:");
  Serial.println(islimit0);
  
  //モーターを端っこまで動かす
  while (true) { 
    stepper.runSpeed();
    if (islimit0) {
      break;
    }
    Serial.print("islimi01while:");
    Serial.println(islimit0);
  }

  Serial.print("islimit0外:");
  Serial.println(islimit0);
  
  Serial.println("抜け出した");
  stepper.stop(); //端まで来たら止まる
  stepper.setCurrentPosition(0); //0ポジ設定
  islimit0 = islimit1 = false;
  delay(1000);

  Serial.println("真ん中いくよ");
  //モーターを真ん中まで動かす
  stepper.moveTo(2500);
  stepper.setSpeed(2000);
  while (true) { 
    stepper.runSpeedToPosition();
    Serial.println(stepper.currentPosition());
    if(stepper.currentPosition()==2500){
      break;
    }
  }

  //モーターを端っこまで動かす
  while (true) { 
    stepper2.runSpeed();
    if (islimit2) {
      break;
    }
    Serial.print("islimi01while:");
    Serial.println(islimit2);
  }

  Serial.print("islimit0外:");
  Serial.println(islimit2);
  
  Serial.println("抜け出した");
  stepper2.stop(); //端まで来たら止まる
  stepper2.setCurrentPosition(0); //0ポジ設定
  islimit2 = islimit3 = false;
  delay(1000);

  Serial.println("真ん中いくよ");
  //モーターを真ん中まで動かす
  stepper2.moveTo(2500);
  stepper2.setSpeed(2000);
  while (true) { 
    stepper2.runSpeedToPosition();
    Serial.println(stepper2.currentPosition());
    if(stepper2.currentPosition()==2500){
      break;
    }
  }

  //モーターを端っこまで動かす
  while (true) { 
    stepper_x.runSpeed();
    if (islimitx0) {
      break;
    }
    Serial.print("islimi01while:");
    Serial.println(islimitx0);
  }

  Serial.print("islimit0外:");
  Serial.println(islimitx0);
  
  Serial.println("抜け出した");
  stepper_x.stop(); //端まで来たら止まる
  stepper_x.setCurrentPosition(0); //0ポジ設定
  islimitx0 = islimitx1 = false;
  delay(1000);

  Serial.println("真ん中いくよ");
  //モーターを真ん中まで動かす
  stepper_x.moveTo(2500);
  stepper_x.setSpeed(2000);
  while (true) { 
    stepper_x.runSpeedToPosition();
    Serial.println(stepper_x.currentPosition());
    if(stepper_x.currentPosition()==2500){
      break;
    }
  }



  
//  stepper.stop(); //端まで来たら止まる
//  stepper.moveTo(-2500);
//  stepper.setSpeed(-2000);
//  while (true) { 
//    stepper.runSpeedToPosition();
//    Serial.println(stepper.currentPosition());
//    if(stepper.currentPosition()==-2500){
//      break;
//    }
//  }  
//  stepper.stop(); //端まで来たら止まる
}
  
void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil(';');
    move_position = line.toInt();
    stepper.move(move_position);
    stepper.setSpeed(2000);
    while (true) { //モーターが端っこに来るまで動く
      stepper.runSpeedToPosition();
      if (stepper.currentPosition()==(move_position+25000)){
        break;
      }
    }
    stepper.stop(); //端まで来たら止まる
    Serial.println("x_measure_end");
  }
}
