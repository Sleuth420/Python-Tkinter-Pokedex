import logging
import os
import time

logger = logging.getLogger(__name__)

if os.name == 'posix':
    try:
        import RPi.GPIO as GPIO
    except ModuleNotFoundError:
        logger.warning("RPi.GPIO not found. Using Mock.GPIO for testing.")
        import Mock.GPIO as GPIO
elif os.name == 'nt':
    import Mock.GPIO as GPIO

    logger.info("Using Mock.GPIO for input handling")
else:
    logger.warning("Unsupported operating system. Input handling will be unavailable.")


class InputHandler:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing InputHandler on {os.name}")

        self.last_pin_state = {}

        # Button pin mapping
        self.button_pins = {
            "up": 25,
            "down": 23,
            "left": 17,
            "right": 24,
            "a": 26,
            "b": 16,
            "start": 13,
            "select": 6
        }

        # Button handler mapping
        self.button_handlers = {
            "up": self.app.handle_up,
            "down": self.app.handle_down,
            "left": self.app.handle_left,
            "right": self.app.handle_right,
            "a": self.app.handle_select,
            "b": self.app.handle_back,
            "start": self.app.handle_start,
            "select": self.app.handle_favourite_toggle
        }

        self.setup_gpio()
        self.last_pressed_time = {button: 0 for button in self.button_pins}

    def setup_gpio(self):
        if os.name == 'posix':
            try:
                GPIO.setmode(GPIO.BCM)
                self.logger.debug("GPIO set to BCM mode.")

                for button_name, pin in self.button_pins.items():
                    try:
                        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                        self.logger.info(f"GPIO pin {pin} ({button_name}) setup successful.")
                    except Exception as e:
                        self.logger.error(f"Error setting up GPIO pin {pin} ({button_name}): {e}")

            except Exception as e:
                self.logger.exception(f"GPIO Initialization failed: {e}")

    def check_gpio_input(self):
        if os.name == 'posix':
            try:
                for button, pin in self.button_pins.items():
                    pin_state = GPIO.input(pin)

                    # Log only if the state has changed
                    if pin_state != self.last_pin_state.get(button, 1):  # Default to 1 (unpressed)
                        self.logger.debug(f"Checking pin {pin} ({button}): State = {pin_state}")
                        self.last_pin_state[button] = pin_state

                    if not pin_state:  # Button pressed
                        current_time = time.time()
                        if current_time - self.last_pressed_time[button] > 0.2:  # Debounce
                            self.logger.info(f"{button} button pressed on pin {pin}")

                            handler = self.button_handlers.get(button)
                            if handler:
                                try:
                                    handler()
                                    self.logger.debug(f"Handler for {button} executed successfully.")
                                except Exception as e:
                                    self.logger.exception(f"Error in handler for {button}: {e}")

                            self.last_pressed_time[button] = current_time
                        time.sleep(0.05)
                        return

            except Exception as e:
                self.logger.exception(f"Error checking GPIO input: {e}")

            finally:
                self.app.master.after(100, self.check_gpio_input)  # Poll every 100ms
