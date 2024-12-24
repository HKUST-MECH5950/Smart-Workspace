#include <Arduino.h>
#include <Button.h>

Button::Button(int buttonPin){
  pin = buttonPin;
  debounceDelay = 1000;
  pinMode(pin, INPUT);
  ButtonState = LOW;
  lastButtonState = LOW;
  lastDebounceTime = 0;
};

bool Button::check(){
  int reading = digitalRead(pin); 
  if (reading != lastButtonState) {
    lastDebounceTime = millis(); 
  }
  if ((millis() - lastDebounceTime) > debounceDelay) {
    ButtonState = reading;
  }
  lastButtonState = reading; 
  return ButtonState; 
}
