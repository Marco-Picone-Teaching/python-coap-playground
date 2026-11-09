import asyncio
import time

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat

from coap_playground.dto.message_descriptor import MessageDescriptor
from coap_playground.model.temperature_sensor import TemperatureSensor


class ObsTemperatureSensorResource(resource.ObservableResource):
    """ Example of an Observable Temperature Sensor resource (RFC 7641).
    A background asyncio task periodically measures a new value and calls updated_state()
    to send a notification to all the registered observers """

    def __init__(self, update_period_s: float = 5.0) -> None:
        """ Constructor for ObsTemperatureSensorResource class
        :param update_period_s: Period in seconds between two consecutive measurements
        """
        super().__init__()
        self.temperature_sensor = TemperatureSensor()
        self.update_period_s = update_period_s

        # Reference to the measurement task (created by start_measurements() once the event loop is running)
        self.measurement_task: asyncio.Task[None] | None = None

    def start_measurements(self) -> None:
        """ Start the periodic measurement task. It must be called when the asyncio event loop is running """
        if self.measurement_task is None:
            self.measurement_task = asyncio.create_task(self.measurement_loop())

    async def measurement_loop(self) -> None:
        """ Periodically measure a new temperature value and notify the observers """

        while True:
            # Non-blocking sleep: the event loop keeps serving the incoming requests in the meantime
            # (a time.sleep() would block the whole server)
            await asyncio.sleep(self.update_period_s)

            self.temperature_sensor.measure_temperature()
            print("\n##################################")
            print(f"Updated Temperature Value: {self.temperature_sensor.temperature_value:.2f}")
            print("Update Status & Notify Observers ...")

            # aiocoap calls render_get() for each observer and sends the notification
            # with an increasing value of the Observe option
            self.updated_state()
            print("##################################")

    def update_observation_count(self, newcount: int) -> None:
        """ Hook called by aiocoap when the number of observers changes """
        print(f"Number of active observers: {newcount}")

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        """ GET: return the current temperature value (used both for normal GET requests and notifications) """

        print(f"GET Request Received - Current Temperature Value: {self.temperature_sensor.temperature_value:.2f}")

        payload_string = MessageDescriptor(int(time.time()),
                                           "TEMPERATURE_SENSOR",
                                           self.temperature_sensor.temperature_value).to_json()

        return aiocoap.Message(content_format=ContentFormat.JSON, payload=payload_string.encode("utf-8"))
