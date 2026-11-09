import time
from typing import Any

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat
from kpn_senml import SenmlPack, SenmlRecord

from coap_playground.model.switch_actuator import SwitchActuator

# Content Format of the resource: application/senml+json (110)
SENML_JSON_CONTENT_FORMAT = ContentFormat.by_media_type("application/senml+json")


class CoreSwitchActuatorResource(resource.Resource):
    """ Switch Actuator resource following the CoRE Interfaces Actuator interface (core.a):
    - GET: read the current status (SenML JSON)
    - PUT: set a new status ("true" or "false" as plain text payload)
    - POST: toggle the status (no payload) """

    def __init__(self, device_name: str) -> None:
        """ Constructor for CoreSwitchActuatorResource class
        :param device_name: Name of the device used as SenML Base Name
        """
        super().__init__()

        # CoRE Link Format attributes used by aiocoap to build the /.well-known/core description
        self.if_ = "core.a"                                   # Interface Description: CoRE Interfaces - Actuator
        self.ct = int(SENML_JSON_CONTENT_FORMAT)              # Content Type (as integer identifier)
        self.rt = "it.unimore.device.actuator.switch"         # Resource Type (application specific)
        self.title = "Switch Actuator"                        # Human readable title

        self.device_name = device_name
        self.actuator = SwitchActuator()

    def get_link_description(self) -> dict[str, Any]:
        """ Extend the default link description (ct, rt, if) with the title attribute """
        link = super().get_link_description()
        link["title"] = self.title
        return link

    def build_senml_json_payload(self) -> str:
        """ Build the SenML JSON payload with the current switch status (Boolean Value field: vb) """
        pack = SenmlPack(self.device_name)
        pack.add(SenmlRecord("switch", value=self.actuator.switch_status, time=int(time.time())))
        return pack.to_json()

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        """ GET: return the current switch status as SenML JSON """

        print(f"GET Request Received - Current Switch Status: {self.actuator.switch_status}")

        payload_string = self.build_senml_json_payload()
        return aiocoap.Message(content_format=SENML_JSON_CONTENT_FORMAT, payload=payload_string.encode("utf-8"))

    async def render_post(self, request: aiocoap.Message) -> aiocoap.Message:
        """ POST (with no body): toggle the switch status """

        self.actuator.change_switch_status()
        print(f"POST Request Received - Switch Status toggled to: {self.actuator.switch_status}")

        return aiocoap.Message(code=aiocoap.CHANGED)

    async def render_put(self, request: aiocoap.Message) -> aiocoap.Message:
        """ PUT: set the switch status from a "true" / "false" plain text payload """

        payload_string = request.payload.decode("utf-8").strip().lower()
        print(f"PUT Request Received - Payload: {payload_string}")

        if payload_string == "true":
            self.actuator.set_switch_status(True)
        elif payload_string == "false":
            self.actuator.set_switch_status(False)
        else:
            # The payload is not valid: 4.00 Bad Request
            print("Invalid payload -> 4.00 Bad Request")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

        print(f"Switch Status set to: {self.actuator.switch_status}")
        return aiocoap.Message(code=aiocoap.CHANGED)
