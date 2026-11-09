import random


class TemperatureSensor:
    """ This class represents a temperature sensor that can measure the temperature in the environment
    generating random values between 20.0 and 40.0 """

    def __init__(self) -> None:
        """ Constructor for TemperatureSensor class """

        # Set the initial temperature value to 0.0
        self.temperature_value: float = 0.0

        # Call the measure_temperature method to generate the first value
        self.measure_temperature()

    def measure_temperature(self) -> None:
        """ Method to generate a random temperature value between 20.0 and 40.0 """

        # Generate a random temperature value between 20.0 and 40.0
        self.temperature_value = random.uniform(20.0, 40.0)
