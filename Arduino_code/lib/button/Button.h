#include <Arduino.h>

class Button {
  private:
    int pin;                       // Pin number for the button
    int ButtonState;          // Previous state of the button
    int lastButtonState;          // Previous state of the button
    unsigned long lastDebounceTime; // Last time the button state was changed
    unsigned long debounceDelay;  // Debounce delay

  public:
    // Constructor
    Button(int buttonPin);
    bool check();
};