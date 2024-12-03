import time

class AirConditioner:
    def __init__(self):
        self.state = False
        self.mode = "cool"
        self.temperature = 24

    def turn_on(self):
        self.state = True
        print("Air Conditioner is now ON.")

    def turn_off(self):
        self.state = False
        print("Air Conditioner is now OFF.")

    def set_mode(self, mode):
        self.mode = mode
        print(f"Air Conditioner mode set to {self.mode}.")

    def set_temperature_add(self):
        self.temperature = self.temperature+1
        print(f"Air Conditioner temperature set to {self.temperature}°C.")

    def set_temperature_reduce(self):
        self.temperature = self.temperature-1
        print(f"Air Conditioner temperature set to {self.temperature}°C.")

    def get_status(self):
        return self.state

    def get_mode(self):
        return self.mode

    def get_temperature(self):
        return self.temperature

# Test code
if __name__ == "__main__":
    ac = AirConditioner()
    ac.turn_on()
    ac.set_mode("heat")
    ac.set_temperature(26)
    time.sleep(1)
    ac.turn_off()