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

//緊急停止ボタン
#define STOP_PIN 14
#define CALIBSPEED -10000

bool islimit0_x = false;
bool islimit1_x = false;
bool islimit0_y = false;
bool islimit1_y = false;
bool islimit0_z = false;
bool islimit1_z = false;
bool STOP = false;
bool fmoving=false;
bool pmoving=false;

long setSpx=0;
long setSpy=0;
long setSpz=0;

long getxsp;
long getxpos;
long getysp;
long getypos;
long getzsp;
long getzpos;

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

//緊急停止割り込み用関数・外部割り込みピンはリミットセンサで使用済みのためD14番に対してピン変化割り込み(PCINT)
ISR(PCINT1_vect) {
  STOP = true;
  Serial.println("Emergency STOP");
  digitalWrite(STEPPER_PULSE_PIN_x, LOW);
  digitalWrite(STEPPER_CCW_PIN_x, LOW);
  digitalWrite(STEPPER_PULSE_PIN_y, LOW);
  digitalWrite(STEPPER_CCW_PIN_y, LOW);
  digitalWrite(STEPPER_PULSE_PIN_z, LOW);
  digitalWrite(STEPPER_CCW_PIN_z, LOW);
  //停止用
  while (true) {
  }
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
void moveXYZ(long x_speed,long x_position,long y_speed,long y_position,long z_speed,long z_position,long zforce){
  stepper_x.moveTo(x_position);
  stepper_y.moveTo(y_position);
  stepper_z.moveTo(z_position);

  // ステッパーの速度を設定
  stepper_x.setSpeed(x_speed);
  stepper_y.setSpeed(y_speed);
  stepper_z.setSpeed(z_speed);

  // 1ステップずつ動作を確認
  if (pmoving) {
    if (stepper_x.currentPosition() != x_position) {
      stepper_x.runSpeedToPosition();
      } else {
      Serial.println("x stop");
      }

    if (stepper_y.currentPosition() != y_position) {
      stepper_y.runSpeedToPosition();
      } else {
      Serial.println("y stop");
      }

    if (stepper_z.currentPosition() != z_position && zforce <= 15) {
      stepper_z.runSpeedToPosition();
      } else {
      Serial.println("z stop");
      }

    // 現在の位置を表示
    Serial.print("x = ");
    Serial.println(stepper_x.currentPosition());
    Serial.print("y = ");
    Serial.println(stepper_y.currentPosition());
    Serial.print("z = ");
    Serial.println(stepper_z.currentPosition());

    // すべてのモーターが停止したか確認
    if (stepper_x.currentPosition() == x_position && stepper_y.currentPosition() == y_position && stepper_z.currentPosition() == z_position) {
      pmoving = false;  // 動作終了
      Serial.println("Done");      
      }
    }
  }

//ロボットステージを動かす
void moveToForceX(float x_speed){
    stepper_x.setSpeed(x_speed);
    stepper_x.runSpeed();
    Serial.println(stepper_x.currentPosition());
    Serial.println("moving");
  }

void moveToForceY(float y_speed){
    stepper_y.setSpeed(y_speed);
    stepper_y.runSpeed();
    Serial.println(stepper_y.currentPosition());
    Serial.println("moving");
  }

void moveToForceZ(long z_speed) {
    stepper_z.setSpeed(z_speed);
    stepper_z.runSpeed();
    Serial.println(stepper_z.currentPosition());
    Serial.println("moving");
}


void Stop(){
    stepper_z.disableOutputs();
    stepper_y.disableOutputs();
    stepper_x.disableOutputs();
    Serial.println("stoping");        
  }
  
void SerialRead(){
    if(Serial.available()>0){
    String input = Serial.readStringUntil('\n');
    if(input == "Cal"){
      STOP = false;
      Serial.println("receve cal");
      Calibration();    
      }
    if(input == "STOP"){
      STOP = true;      
      fmoving = false;
      pmoving = false;
      Serial.println("receve stop");
      Stop();
      }
    else if(ReceiveDataNum(input)==5){
      STOP = false;
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
      getxsp = xsp;
      getxpos = xpos;
      getysp = ysp;
      getypos = ypos;
      getzsp = zsp;
      getzpos = zpos;
      pmoving = true;
      fmoving = false;
      //moveXYZ(xsp,xpos,ysp,ypos,zsp,zpos,0);           
      }
    else if(ReceiveDataNum(input)==2){
      STOP = false;
      int indexXf = input.indexOf(',');
      int indexYf = input.indexOf(',',indexXf+1);
      int indexZf = input.indexOf(',',indexYf+1);
      long x,y,z;
      x = input.substring(0, indexXf).toInt();
      y = input.substring(indexXf+1, indexYf).toInt();
      z = input.substring(indexYf+1).toInt();
      setSpx = x;
      setSpy = y;
      setSpz = z;
      fmoving = true;
      pmoving = false;
      }
    }
  }

//受信したコマンドの制御個数を返す関数
int ReceiveDataNum(String input){
  int count = 0;
  for(int i=0;i<input.length();i++){
    if(input.charAt(i)==','){
      count++;
      }
    }
  return count;
  }
//セットアップ  
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
  pinMode(STOP_PIN, INPUT_PULLUP);
  //リミットセンサ割り込み
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_x), flag_0, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_x), flag_1, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_y), flag_2, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_y), flag_3, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN_z), flag_4, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN_z), flag_5, RISING);
  //緊急停止ボタン割り込み
  PCICR |= (1 << PCIE1);            // PCINT10があるレジスタを割り込みに設定
  PCMSK1 |= (1 << PCINT10);         // PCINT10（D14ピン)で緊急停止ボタン割り込み
  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor
  stepper_x.setMaxSpeed(10000);  // 脱調防止
  stepper_y.setMaxSpeed(10000);  // 脱調防止
  stepper_z.setMaxSpeed(10000);  // 脱調防止
  Serial.println("Setup");
}
      
void loop() {
  SerialRead();
  if(!STOP){
  //loop内記述
    if(fmoving){
      moveToForceX(setSpx);
      moveToForceY(setSpy);      
      moveToForceZ(setSpz);
      }
    if(pmoving){
      moveXYZ(getxsp,getxpos,getysp,getypos,getzsp,getzpos,0);
      }
  }else{
    Stop();
    Serial.println("Done");
    }
  //Serial.println(STOP);
}
