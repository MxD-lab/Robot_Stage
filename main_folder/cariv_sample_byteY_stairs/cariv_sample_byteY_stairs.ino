/*
  2022/07/29（金）記入者：船橋佑｜xyzのキャリブレーション後、z軸の計測のみ行う。その際、計測してからの反映がserialだと遅いので、計測時のみ2000pulse/秒ではなく100pulse/秒でおこなう。
  2022/08/01（月）記入者：船橋佑｜よく使うlimit制御で移動するコードと指定した位置まで移動するコードを関数化した
  2022/08/02（火）記入者：船橋裕｜各ループのなかを整理した。基本はシリアルを受け付けるだけのループであり、指定した文字がくると実行したいコードのフラグを切り替える。
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
bool serial_flag3 = false;
bool serial_flag4 = false;
bool serial_flag5 = false;
bool serial_flag6 = false;
bool serial_flag7 = false;

String data;
int x_position;

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
      serial_flag2 = false;
//      Serial.println("move_z_end");
    }
  }
}

void Z_suport(){
  
  if (Serial.available()) {
    String line2 = Serial.readStringUntil(';');
    if (line2.equals("Z-")) {
      stepper_z.setSpeed(-1);
    }else if(line2.equals("Z+")){
      stepper_z.setSpeed(1);
    }else{
      stepper_z.setSpeed(0);
//      stepper_z.stop();
    }
  }
  Serial.flush();
}

void run_speed(AccelStepper axis){
  while (true) { //モーターが端っこに来るまで動く
    axis.runSpeed();
    stop_check();  
    if (islimit0_x==true|islimit1_x==true|islimit0_y==true|islimit1_y==true|islimit0_z==true|islimit1_z==true) {
      break;
    }
  }
  axis.stop(); //端まで来たら止まる
  axis.setCurrentPosition(0); //0ポジ設定
}  

//ここにｚ軸補正を入れたい
int move_to(AccelStepper axis,int distance,int pulse){
  stepper_z.setSpeed(0);
  axis.moveTo(distance);
  axis.setSpeed(pulse);
  while (!(axis.currentPosition() == distance)) {
    axis.runSpeedToPosition();
    Z_suport();
    stepper_z.runSpeed();
    stop_check();
  }
  return axis.currentPosition();
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
  //Serial.println("start");

  while (true) {
    if (Serial.available()) {
      data = Serial.readStringUntil(';');
     
      if (data.equals("1")) {
        serial_flag1 = true;
      }else if(data.equals("2")){
        serial_flag2 = true;
      }
    }

    if(serial_flag1){
      run_speed(stepper_z);
      islimit0_z =false;
      delay(1000);
      serial_flag1 = false;
      Serial.println("1");

      
    }else if(serial_flag2){
      
      run_speed(stepper_x);
      delay(1000);
      x_position = move_to(stepper_x, 25000, 2000);
      islimit0_x =false;
      delay(1000);
     
      run_speed(stepper_y);
      delay(1000);
      move_to(stepper_y, 25000, 2000);
      islimit0_y =false;
      delay(1000);
            
      serial_flag2 = false;
      Serial.println("2");
      break;
    }
  }
}
      



void loop() {
  if (Serial.available()) {
    data = Serial.readStringUntil(';');
    if(data.equals("3")){
      serial_flag3 = true;
    } else if (data.equals("4")){
      serial_flag4 = true;
    } else if (data.equals("5")){
      serial_flag5 = true;
    }else if (data.equals("6")){
      serial_flag6 = true;
    }else if (data.equals("7")){
      serial_flag7 = true;
    }
  }

  if(serial_flag3){
    //move_to(stepper_z, 23000, 2000);
    stepper_z.moveTo(36000);
    stepper_z.setSpeed(2000); 
    while (!(stepper_z.currentPosition() == 36000)) {
      stepper_z.runSpeedToPosition();
    } 
    stepper_z.moveTo(40000);
    stepper_z.setSpeed(10);
    //Serial.flush();
    while(true){
      //Serial.println(data);
      //stepper_z.runSpeed();

      stepper_z.runSpeedToPosition();
      if(Serial.available()){
        data = Serial.readStringUntil(';');
        if(data.equals("8") | data.equals("9")){
          //Serial.println(data);
          Serial.println("3");
          stepper_z.stop();
          break;
        }
      }
    }
    serial_flag3 = false;
  }else if (serial_flag4){
    x_position = move_to(stepper_x, 300, 100);
    Serial.println("4");
    stepper_x.stop();
    serial_flag4 = false;
  }else if (serial_flag5){
    move_to(stepper_y, 800, 100);
    Serial.println("5");
   // stepper_y.stop();
    serial_flag5 = false;
  }else if (serial_flag6){
    stepper_z.setSpeed(-1000);
    run_speed(stepper_z);
    Serial.println("6");
//    stepper_z.stop();
    serial_flag6 = false;
  }else if(serial_flag7){
    stepper_z.setSpeed(CARIVSPEED);
    run_speed(stepper_z);
    islimit0_z =false;
    move_to(stepper_y, -800, -2000);
    stepper_z.setCurrentPosition(0);
    Serial.println(stepper_z.currentPosition());
    delay(1000);
    Serial.println("7");
    serial_flag7 = false;
  }
}
