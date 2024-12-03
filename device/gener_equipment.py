import time
class GeneralEquipment:
    def __init__(self, device_id):
        self.device_id = device_id
        self.state = False

    def turn_on(self):
        self.state = True
        print(f"device {self.device_id} is now ON.")

    def turn_off(self):
        self.state = False
        print(f"device {self.device_id} is now OFF.")

    def get_status(self):
        return self.state

# Test code
if __name__ == "__main__":
    device1 = device(1)
    device1.turn_on()
    time.sleep(1)
    device1.turn_off()