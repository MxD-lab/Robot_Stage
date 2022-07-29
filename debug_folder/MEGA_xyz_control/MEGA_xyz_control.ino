
/*
2022/06/27（月）記入者：船橋佑｜xyzのキャリブレーションを行ったのち、自由に制御するコード作成
2022/06/28（火）記入者：船橋佑｜xyのキャリブレーションを行うことに成功。zはリミットセンサが死んでいるのか断線しているのかわからないが反応がない。しかし、zに関しては相対位置で制御すればよいと判断したためこのまま続行
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
  stepper_y.setSpeed(CARIVSPEED);
  stepper_z.setMaxSpeed(2000);  // 脱調防止
  stepper_z.setSpeed(CARIVSPEED);


  while(true){
    if (Serial.available()) {
      String line = Serial.readStringUntil(';');
      //Serial.println("hoge1");
      if (line.equals("cariv_start")) {
        Serial.flush();
        while (true) { //モーターが端っこに来るまで動く 
          stepper_x.runSpeed();
          if (islimit0_x) {
            break;
          }else if(Serial.available()){
            String line2 = Serial.readStringUntil(';');
            if (line2.equals("stop")) {
              Serial.println("hogehogehoge3");
              break;
            }
          }
        }
        stepper_x.stop(); //端まで来たら止まる
        stepper_x.setCurrentPosition(0); //0ポジ設定
        islimit0_x = islimit1_x = false;
        delay(1000);
  
        //モーターを真ん中まで動かす
        stepper_x.moveTo(25000);
        stepper_x.setSpeed(2000);
        while (true) { 
          stepper_x.runSpeedToPosition();
          if(stepper_x.currentPosition()==25000){
            break;
          }
        }  
        //stepper_x.stop(); //端まで来たら止まる
        delay(1000);

        while (true) { //モーターが端っこに来るまで動く
          stepper_y.runSpeed();
          if (islimit0_y) {
            break;
          }
        }
        stepper_y.stop(); //端まで来たら止まる
        stepper_y.setCurrentPosition(0); //0ポジ設定
        islimit0_y = islimit1_y = false;
        delay(1000);
  
        //モーターを真ん中まで動かす
        stepper_y.moveTo(30000);
        stepper_y.setSpeed(2000);
        while (true) { 
          stepper_y.runSpeedToPosition();
          if(stepper_y.currentPosition()==30000){
            break;
          }
        }  
        //stepper_y.stop(); //端まで来たら止まる
        delay(1000);
    
        while (true) { //モーターが端っこに来るまで動く 
          stepper_z.runSpeed();
          if (islimit0_z) {
            break;
          }
        }
        stepper_z.stop(); //端まで来たら止まる
        stepper_z.setCurrentPosition(0); //0ポジ設定
        islimit0_z = islimit1_z = false;
        delay(1000);
  
        //モーターを真ん中まで動かす
        stepper_z.moveTo(25000);
        stepper_z.setSpeed(2000);
        while (true) { 
          stepper_z.runSpeedToPosition();
          if(stepper_z.currentPosition()==25000){
            break;
          }
        }  
        //stepper_z.stop(); //端まで来たら止まる
        delay(1000);

        Serial.println("cariv_end");
        break;
      }
    }
  }
  //stepper_z.setCurrentPosition(0); //0ポジ設定
  Serial.println(stepper_z.currentPosition());
  Serial.println(stepper_x.currentPosition());
}

void loop() {
  byte ver = Serial.read();
  switch(ver){
    case '1':
      Serial.println("move_x_start");
      stepper_x.moveTo(26000);
      stepper_x.setSpeed(2000);
      while (true) { //モーターが端っこに来るまで動く
        stepper_x.runSpeedToPosition();
        if (stepper_x.currentPosition()==(26000)){
          break;
        }
      }
      stepper_x.stop(); //端まで来たら止まる
      Serial.println("move_x_end");
      break;

    case '2':
      Serial.println("move_x_start");
      stepper_x.moveTo(24000);
      stepper_x.setSpeed(-2000);
      Serial.println(stepper_x.currentPosition());
      while (true) { //モーターが端っこに来るまで動く
        stepper_x.runSpeedToPosition();
        if (stepper_x.currentPosition()==(24000)){
          break;
        }
      }
      stepper_x.stop(); //端まで来たら止まる
      Serial.println("move_x_end");
      break;

    case '3':
      Serial.println("move_y_start");
      stepper_y.moveTo(31000);
      stepper_y.setSpeed(2000);
      while (true) { //モーターが端っこに来るまで動く
        stepper_y.runSpeedToPosition();
        if (stepper_y.currentPosition()==(31000)){
          break;
        }
      }
      stepper_y.stop(); //端まで来たら止まる
      Serial.println("move_y_end");
      break;

    case '4':
      Serial.println("move_y_start");
      stepper_y.moveTo(29000);
      stepper_y.setSpeed(-2000);
      while (true) { //モーターが端っこに来るまで動く
        stepper_y.runSpeedToPosition();
        if (stepper_y.currentPosition()==(29000)){
          break;
        }
      }
      stepper_y.stop(); //端まで来たら止まる
      Serial.println("move_y_end");
      break;

    case '5':
      Serial.println("move_z_start");
      stepper_z.moveTo(1000);
      stepper_z.setSpeed(2000);
      Serial.println(stepper_z.currentPosition());
      while (true) { //モーターが端っこに来るまで動く
        stepper_z.runSpeedToPosition();
        Serial.println(stepper_z.currentPosition());
        if (stepper_z.currentPosition()==(1000)){
          stepper_z.setCurrentPosition(0);
          break;
        }
      }
      stepper_z.stop(); //端まで来たら止まる      
      Serial.println("move_z_end");
      break;

    case '6':
      Serial.println("move_z_start");
      stepper_z.moveTo(-1000);
      stepper_z.setSpeed(-2000);
      Serial.println(stepper_z.currentPosition());
      while (true) { //モーターが端っこに来るまで動く
        stepper_z.runSpeedToPosition();
        Serial.println(stepper_z.currentPosition());
        if (stepper_z.currentPosition()==(-1000)){
          stepper_z.setCurrentPosition(0);
          break;
        }
      }
      stepper_z.stop(); //端まで来たら止まる
      Serial.println("move_z_end");
      break;
  }
}
