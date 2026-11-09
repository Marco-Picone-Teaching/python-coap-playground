import asyncio
import time
from typing import Any

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat
from kpn_senml import SenmlPack, SenmlRecord, SenmlUnits

from coap_playground.model.temperature_sensor import TemperatureSensor

# Content Format of the resource: application/senml+json (110)
SENML_JSON_CONTENT_FORMAT = ContentFormat.by_media_type("application/senml+json")


class CoreTemperatureSensorResource(resource.ObservableResource):
    """ Observable Temperature Sensor resource described with the CoRE Link Format attributes
    (rt, if, ct, title, obs) and returning SenML JSON payloads """

    def __init__(self, device_name: str, update_period_s: float = 5.0) -> None:
        """ Constructor for CoreTemperatureSensorResource class
        :param device_name: Name of the device used as SenML Base Name
        :param update_period_s: Period in seconds between two consecutive measurements
        """
        super().__init__()

        # CoRE Link Format attributes used by aiocoap to build the /.well-known/core description
        self.if_ = "core.s"                                   # Interface Description: CoRE Interfaces - Sensor
        self.ct = int(SENML_JSON_CONTENT_FORMAT)              # Content Type (as integer identifier)
        self.rt = "it.unimore.device.sensor.temperature"      # Resource Type (application specific)
        self.title = "Temperature Sensor"                     # Human readable title

        self.device_name = device_name
        self.update_period_s = update_period_s
        self.temperature_sensor = TemperatureSensor()
        self.measurement_task: asyncio.Task[None] | None = None

    def get_link_description(self) -> dict[str, Any]:
        """ Extend the default link description (ct, rt, if, obs) with the title attribute """
        link = super().get_link_description()
        link["title"] = self.title
        return link

    def start_measurements(self) -> None:
        """ Start the periodic measurement task. It must be called when the asyncio event loop is running """
        if self.measurement_task is None:
            self.measurement_task = asyncio.create_task(self.measurement_loop())

    async def measurement_loop(self) -> None:
        """ Periodically measure a new temperature value and notify the observers """
        while True:
            await asyncio.sleep(self.update_period_s)
            self.temperature_sensor.measure_temperature()
            print(f"Updated Temperature Value: {self.temperature_sensor.temperature_value:.2f} -> Notify Observers")
            self.updated_state()

    def build_senml_json_payload(self) -> str:
        """ Build the SenML JSON payload with the current temperature value """
        pack = SenmlPack(self.device_name)
        pack.add(SenmlRecord("temperature",
                             unit=SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
                             value=self.temperature_sensor.temperature_value,
                             time=int(time.time())))
        return pack.to_json()

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        """ GET: return the current temperature value as SenML JSON """

        print(f"GET Request Received - Current Temperature Value: {self.temperature_sensor.temperature_value:.2f}")

        payload_string = self.build_senml_json_payload()
        return aiocoap.Message(content_format=SENML_JSON_CONTENT_FORMAT, payload=payload_string.encode("utf-8"))
