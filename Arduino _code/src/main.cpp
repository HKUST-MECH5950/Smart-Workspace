#include <Arduino.h>
#include <Adafruit_LiquidCrystal.h>
#include <DHT.h>
#include <Button.h>
#include <PID_v1.h>


#define RGB_R_Out 3 //RGB-LED-R
#define RGB_G_Out 6 //RGB-LED-G
#define RGB_B_Out 5 //RGB-LED-B

//human detect
#define IR_Sensor_In 9 //IR
#define lamp_Out 10 //lamp
#define Photo_In A1 //Photo sensor

//Temperature sersing
#define Fan_Out 8 //Fan
#define Temp_In 13 //Temp sensor

//Sit monitor
#define Button_In 2
#define Led_Out 11

//all sersor input
bool ir_read = 0;
int photo_read = 0;
float temp_read = 0.;
float humi_read = 0.;
bool button_read = 0;
bool last_button_read = 0;

//all actuator output
bool r_out = 0;
bool g_out = 0;
bool b_out = 0;
bool fan_out = 0;
int lamp_out = 0;
bool led_out = 0;


//memory
unsigned long startTime = 0; // time when the button is pressed
unsigned long elapsedTime = 0; // elapsed time since the button was pressed
unsigned long cTime = 0; // elapsed time since the button was pressed
unsigned long lastTime = 0; // elapsed time since the button was pressed

bool debug = 1;
unsigned long lastdbTime = 0;
int Photo_seneor_th  = 0;
int temp_hot_th = 27;
unsigned int Sit_duration = 1000; // 3600000


DHT dht(Temp_In, DHT11);

String s_string = "";

double l_in, l_out, l_t; 
PID lamp_pid(&l_in, &l_out, &l_t, 0.5, 0.1, 0.01, DIRECT);
// PID lamp_pid(&l_in, &l_out, &l_t, 0.005, 0.005, 0.0001, DIRECT);

Button sit_button(Button_In);

void getReadableTime(String &readableTime) {
  unsigned long currentMillis;
  unsigned long seconds;
  unsigned long minutes;
  unsigned long hours;


  currentMillis = elapsedTime;
  seconds = currentMillis / 1000;
  minutes = seconds / 60;
  hours = minutes / 60;

  currentMillis %= 1000;
  seconds %= 60;
  minutes %= 60;
  hours %= 24;

  if (hours < 10) {
    readableTime += "0";
  }
    readableTime += String(hours) + "h:";


  if (minutes < 10) {
    readableTime += "0";
  }
  readableTime += String(minutes) + "m:";

  if (seconds < 10) {
    readableTime += "0";
  }
  readableTime += String(seconds) + "s";
}

void get_current_env_data(){
  ir_read = digitalRead(IR_Sensor_In);
  photo_read = analogRead(Photo_In);
  l_in = double(photo_read);
  temp_read = dht.readTemperature();
  humi_read = dht.readHumidity();
  button_read = sit_button.check();
}

void print_log(){
  unsigned long now = millis();
  if ((now-lastdbTime)>0){
      Serial.println("DB|" + String(temp_read) + " " + String(humi_read));
      // Serial.println(String(ir_read) + " " + String(photo_read) + " " + String(lamp_out));
  //   Serial.println("===========================");
  //   Serial.print("irReading = "); Serial.println(ir_read);
  //   Serial.print("lightReading = "); Serial.println(photo_read);
  //   Serial.print("TempReading = "); Serial.println(temp_read);
  //   Serial.print("buttomReading = "); Serial.println(button_read);
  //   Serial.println("===========================");
  //   lastdbTime = now;
  }
  
}

void update_last(){
  last_button_read = button_read;
  cTime = millis();
  // display.update();
}

void update_output(){
  digitalWrite(RGB_R_Out, r_out);
  digitalWrite(RGB_G_Out, g_out);
  digitalWrite(RGB_B_Out, b_out);
  digitalWrite(Fan_Out, fan_out);
  analogWrite(lamp_Out, lamp_out);
  digitalWrite(Led_Out, led_out);
}

void init_output(){
  r_out = 0;
  g_out = 0;
  b_out = 0;
  fan_out = 0;
  lamp_out = 0;
  update_output();
}

void check_hd(){
  if (ir_read == 1)
  { 
    l_t = double(Photo_seneor_th);
  }else{
    l_t = 0.;
  }
  // Serial.println(Photo_seneor_th);
  // delay(1000);
  lamp_pid.Compute();
  lamp_out = int(l_out);
  // lamp_out = max(min(lamp_out, 255), 0);
    
}

void check_temp(){
  // if (temp_read<=23){
  //   r_out = 0;
  //   g_out = 0;
  //   b_out = 1;
  //   fan_out = 0;
  // }else if (temp_read >= 23 && 
  if (temp_read < temp_hot_th)
  {
    r_out = 0;
    g_out = 1;
    b_out = 0;
    // fan_out = 0;
  }else if (temp_read >= temp_hot_th)
  {
    r_out = 1;
    g_out = 0;
    b_out = 0;
    fan_out = 1;
  }
  
}

void check_sit(){
  if (button_read != last_button_read){
    if (button_read){
      startTime = millis();
    } else {
      elapsedTime = 0; 
      led_out = 0;
    }
  } else {
    if (button_read){
      elapsedTime = millis() - startTime;
      if (elapsedTime >= Sit_duration){
        led_out = 1;
      }
    }
  }
  
}

void check_all(){
  check_hd();
  check_temp();
  check_sit();
}

String readline(){
  char c;
  bool find_end = 0;
  while (!find_end){
    if (Serial.available()){
      c = Serial.read();
      if (c == '\n'){
        find_end = 1;
        String t_s = s_string;
        s_string = "";
        // Serial.println("Echo: " + t_s +"|");
        return t_s;
      } else if (c != '\r') {
        s_string += c;
      }
    }

  }
  
   return "";
}

void send_init_message(){
  String out = "IA|";
  out += "lamp:0;sl,LED:0;tb,FAN:0;tb||IC|";
  out += "Temp:25;f;0;50,Light_level:0;f;0;1023,Sit_duration:1;f;1;10\n";
  Serial.print(out);
}

void send_current_data(){
  String out = "ED|";
  out +="Temp:";
  out += String(float(temp_read)/(50.));
  out +=",Photo:";
  out += String(float(photo_read)/(1023.));
  out +=",IR:";
  out += String(float(ir_read)/(1.));
  out +=",Sit:";
  out += String(float(button_read)/(1.));
  out +=",Humi:";
  out += String(float(humi_read)/(100.));
  out +="||AD|lamp:";
  out += String(float(lamp_out)/(255.));
  out +=",LED:";
  out += String(float(led_out));
  out +=",FAN:";
  out += String(float(led_out));
  out += "\n";

  Serial.print(out);
}

void change_target(String mes){
  int start_ind = 0;
  int end_ind = mes.indexOf(",");
  bool is_end = false;

  while (!is_end)
  { 
    String sub_message;
    if (end_ind == -1)
    {
      sub_message = mes.substring(start_ind);
      is_end = true;
    } 
    else
    {
      sub_message = mes.substring(start_ind, end_ind);
    }
    
    int name_end_ind = sub_message.indexOf(":");
    String name = sub_message.substring(0, name_end_ind);
    int t_val = sub_message.substring(name_end_ind+1).toInt();
    if (name == "Light_level"){
      Photo_seneor_th = t_val;
    } else if (name == "Temp")
    {
      temp_hot_th = t_val;
    } else if (name == "Sit_duration")
    {
      Sit_duration = t_val*1000;
    }
    
    
    start_ind = end_ind + 1;
    end_ind = mes.indexOf(",", start_ind);
  } 
}

void check_messages(){
  if (Serial.available())
  {
    String reading = readline();
    if (reading == "Send data"){
      send_current_data();
    } else if (reading.substring(0,2) == "CT")
    {
      String subreading = reading.substring(3);      
      change_target(subreading);
    }else{
      Serial.print("Echo: "+reading +"\n");
    }
    

  }
}

void read_messages(){

}

void setup() {
  pinMode(RGB_R_Out, OUTPUT);
  pinMode(RGB_G_Out, OUTPUT);
  pinMode(RGB_B_Out, OUTPUT);
  pinMode(lamp_Out, OUTPUT);
  pinMode(Fan_Out, OUTPUT);
  pinMode(Led_Out, OUTPUT);

  pinMode(IR_Sensor_In, INPUT);
  pinMode(Photo_In, INPUT);
  pinMode(Temp_In, INPUT);
  Serial.begin(9600);
  dht.begin();
  lamp_pid.SetOutputLimits(0., 255.);
  lamp_pid.SetMode(AUTOMATIC);

  send_init_message();

}


void loop() {
  
  get_current_env_data();
  // if (debug){print_log();};
  check_all();
  check_messages();

  update_output();
  update_last();
  // delay(1000);
}


