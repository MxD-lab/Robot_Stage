#include <AccelStepper.h>

// GPIO Pin Definition
//X軸のみ
#define STEPPER_PULSE_PIN 11
#define STEPPER_CCW_PIN   10
#define LIMIT_INT0_PIN    2
#define LIMIT_INT1_PIN    3

#define CARIVSPEED -2000
char key; //手元の停止信号用
bool islimit0 = false;
bool islimit1 = false;
float motorspeed;

AccelStepper stepper(
  AccelStepper::DRIVER,
  STEPPER_PULSE_PIN, STEPPER_CCW_PIN
);


void flag_0(){
//  Serial.println("limit0!!!");
  islimit0 = true;
}

void flag_1(){
//  Serial.println("limit1!!!");
  islimit1 = true;
}
void stop_check(){
  if(islimit1){
    Serial.print("計測が終了しました");
//    stepper.stop();
    islimit0 = islimit1 = false;
    while(true){
      stepper.stop();
    }
  }else if(Serial.available()) {
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
  
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT0_PIN),flag_0, RISING);
  attachInterrupt(digitalPinToInterrupt(LIMIT_INT1_PIN),flag_1, RISING);
  // Init Serial
  Serial.begin(115200);
  // Init Stepper Motor
  stepper.setMaxSpeed(2000);  // 脱調防止
//  stepper.setSpeed(1500);

  stepper.setSpeed(CARIVSPEED);

//  while(!islimit0 && !islimit1 || islimit1){ //モーターが端っこに来るまで動く
//    stepper.runSpeed();
//    stop_check();
//  }
  while(true){ //モーターが端っこに来るまで動く
    stepper.runSpeed();
    if(islimit0){
      break;
    }
  }
 
  stepper.stop(); //端まで来たら止まる
  stepper.setCurrentPosition(0); //0ポジ設定
//  Serial.println(stepper.currentPosition());

    
  islimit0 = islimit1 = false;

  delay(100);
  while(true){
    if (Serial.available()) {
    String line = Serial.readStringUntil(';');
    motorspeed = line.toFloat();
    stepper.setSpeed(motorspeed);
    break;
    }
  }
//  Serial.print("速度は");
//  Serial.print(motorspeed);
//  Serial.println("です");
//  stepper.setSpeed(1200);
}

void loop() {
  stepper.runSpeed();

  stop_check();
   
}
