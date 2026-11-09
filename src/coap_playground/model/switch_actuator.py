

class SwitchActuator:
    """ This class represents a switch actuator that can turn ON or OFF a device """

    def __init__(self) -> None:
        """ Constructor for SwitchActuator class """

        # The switch is ON by default
        self.switch_status: bool = True

    def set_switch_status(self, switch_status: bool) -> None:
        """ Method to set the switch status """
        self.switch_status = switch_status

    def change_switch_status(self) -> None:
        """ Method to change (toggle) the switch status """
        self.switch_status = not self.switch_status
