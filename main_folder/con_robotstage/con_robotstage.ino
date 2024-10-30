/*
  2022/07/29（金）記入者：船橋佑｜xyzのキャリブレーション後、z軸の計測のみ行う。その際、計測してからの反映がserialだと遅いので、計測時のみ2000pulse/秒ではなく100pulse/秒でおこなう。
  2022/08/01（月）記入者：船橋佑｜よく使うlimit制御で移動するコードと指定した位置まで移動するコードを関数化した
  2022/08/02（火）記入者：船橋裕｜各ループのなかを整理した。基本はシリアルを受け付けるだけのループであり、指定した文字がくると実行したいコードのフラグを切り替える。
  2024/10/29 (火)記入者：齋藤竜也｜システム設計の変更キャリブレーションを関数で用意し、呼び出しによって実行するに変更。moveXYZ()を追加
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

#define CALIBSPEED -2000

bool islimit0_x = false;
bool islimit1_x = false;
bool islimit0_y = false;
bool islimit1_y = false;
bool islimit0_z = false;
bool islimit1_z = false;
long move_position;

bool serial_flag1 = false;
bool serial_flag2 = false;

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

//キャリブレーション用関数
void Calibration() {
  islimit0_x = false;
  islimit1_x = false;
  islimit0_y = false;
  islimit1_y = false;
  islimit0_z = false; //z軸上
  islimit1_z = false;
  Serial.println("Calibration now"); 
  while (islimit0_z==false){
    stepper_z.setSpeed(CALIBSPEED);
    stepper_z.runSpeed();
    Serial.println("Calibration z");  
    }
  stepper_z.stop();
  stepper_z.setCurrentPosition(0);
  Serial.println("z fin");
  while (islimit0_y ==false){
    stepper_y.setSpeed(CALIBSPEED);
    stepper_y.runSpeed();
    Serial.println("Calibration y");   
    }
  stepper_y.stop();
  stepper_y.setCurrentPosition(0);
  Serial.println("y fin");
  while (islimit0_x==false){
    stepper_x.setSpeed(CALIBSPEED);
    stepper_x.runSpeed();
    Serial.println("Calibration x");
    }
  stepper_x.stop();
  stepper_x.setCurrentPosition(0);
  Serial.println("x fin");
  Serial.println("fin Calibration");
  }
  
//moveXYZ(x速度(<2000),x座標,y速度(<2000),y座標,z速度(<2000),z座標)
void moveXYZ(long x_speed,long x_position,long y_speed,long y_position,long z_speed,long z_position){
  stepper_x.moveTo(x_position);
  stepper_y.moveTo(y_position);
  stepper_z.moveTo(z_position);
  stepper_x.setSpeed(x_speed);
  stepper_y.setSpeed(y_speed);
  stepper_z.setSpeed(z_speed);  
  while(stepper_x.currentPosition()<=x_position | stepper_y.currentPosition()<=y_position | stepper_z.currentPosition()<=z_position){ 
    if(stepper_x.currentPosition()==x_position){
      stepper_x.stop();
      Serial.println("x stop");
      }
    if(stepper_y.currentPosition()==y_position){
      stepper_y.stop();
      Serial.println("y stop");
      }
    if(stepper_z.currentPosition()==z_position){
      stepper_z.stop();
      Serial.println("z stop");
      }
    stepper_x.runSpeedToPosition();
    stepper_y.runSpeedToPosition();
    stepper_z.runSpeedToPosition();      
    //Serial.println("moving");
    Serial.print("x is =");
    Serial.println(stepper_x.currentPosition());
    Serial.print("y is =");
    Serial.println(stepper_y.currentPosition());
    Serial.print("z is =");
    Serial.println(stepper_z.currentPosition());    
    }
  Serial.println("Done");
  }

void moveX(long x_speed,long x_position){
  stepper_x.moveTo(x_position);
  stepper_x.setSpeed(x_speed);  
  while(stepper_x.currentPosition!=x_position){
    Serial.print("moving");
    Serial.println(stepper_x.currentPosition());    
    stepper_x.runSpeedToPosition();         
    }
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
  //リミットセンサ割り込み
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
  stepper_y.setMaxSpeed(2000);  // 脱調防止
  stepper_z.setMaxSpeed(2000);  // 脱調防止
  Serial.println("Setup");
}
      



void loop() {
  //moveXYZ(1500,25000,1500,27000,1500,10000);
  //moveX(1500,25000);
  if(Serial.available()>0){
    String input = Serial.readStringUntil('\n');
    if(input == "Cal"){
      Calibration();
      //moveXYZ(1000,25000,1000,27000,1000,10000);      
      }
    else{
      int indexXs = input.indexOf(',');
      int indexXp = input.indexOf(',',indexXs+1);
      int indexYs = input.indexOf(',',indexXp+1);
      int indexYp = input.indexOf(',',indexYs+1);
      int indexZs = input.indexOf(',',indexYp+1);

      long xsp = input.substring(0,indexXs).toInt();
      long xpos = input.substring(indexXs+1,indexXp).toInt();
      long ysp = input.substring(indexXp+1,indexYs).toInt();
      long ypos = input.substring(indexYs+1,indexYp).toInt();
      long zsp = input.substring(indexYp+1,indexZs).toInt();
      long zpos = input.substring(indexZs+1).toInt();
      moveXYZ(xsp,xpos,ysp,ypos,zsp,zpos);
                  
      }
    }
  //Serial.println("loop");
}
