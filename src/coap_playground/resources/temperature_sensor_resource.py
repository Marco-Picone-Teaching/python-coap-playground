import time

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat
from kpn_senml import SenmlPack, SenmlRecord, SenmlUnits

from coap_playground.dto.message_descriptor import MessageDescriptor
from coap_playground.model.temperature_sensor import TemperatureSensor

# Content Formats supported by the resource (CoAP Content-Format registry identifiers)
SENML_JSON_CONTENT_FORMAT = ContentFormat.by_media_type("application/senml+json")   # 110
SENML_CBOR_CONTENT_FORMAT = ContentFormat.by_media_type("application/senml+cbor")   # 112
SUPPORTED_CONTENT_FORMATS = [ContentFormat.JSON, ContentFormat.TEXT, SENML_JSON_CONTENT_FORMAT, SENML_CBOR_CONTENT_FORMAT]


class TemperatureSensorResource(resource.Resource):
    """ Example of a Temperature Sensor resource which supports only the GET method.
    The representation is selected through Content Format Negotiation (Accept option):
    application/json (default), text/plain, application/senml+json and application/senml+cbor """

    def __init__(self, device_name: str) -> None:
        """ Constructor for TemperatureSensorResource class
        :param device_name: Name of the device used as SenML Base Name
        """
        super().__init__()
        self.device_name = device_name
        self.temperature_sensor = TemperatureSensor()

    def build_senml_pack(self) -> SenmlPack:
        """ Build a SenML Pack with the current temperature value """

        pack = SenmlPack(self.device_name)
        pack.add(SenmlRecord("temperature",
                             unit=SenmlUnits.SENML_UNIT_DEGREES_CELSIUS,
                             value=self.temperature_sensor.temperature_value,
                             time=int(time.time())))
        return pack

    def build_payload(self, content_format: ContentFormat) -> bytes:
        """ Build the payload of the response in the requested Content Format """

        if content_format == ContentFormat.TEXT:
            return f"{self.temperature_sensor.temperature_value:.2f}".encode("utf-8")
        elif content_format == SENML_JSON_CONTENT_FORMAT:
            return self.build_senml_pack().to_json().encode("utf-8")
        elif content_format == SENML_CBOR_CONTENT_FORMAT:
            # to_cbor() already returns an array of bytes
            return self.build_senml_pack().to_cbor()
        else:
            return MessageDescriptor(int(time.time()),
                                     "TEMPERATURE_SENSOR",
                                     self.temperature_sensor.temperature_value).to_json().encode("utf-8")

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        """ GET: measure a new temperature value and return it in the requested Content Format """

        # The Accept option is None if the client does not specify a preferred Content Format
        requested_format = request.opt.accept
        print(f"GET Request Received - Accept: {int(requested_format) if requested_format is not None else None}")

        # Default representation if the Accept option is not specified
        content_format = requested_format if requested_format is not None else ContentFormat.JSON

        # Content Format Negotiation: 4.06 Not Acceptable if the requested format is not supported
        if content_format not in SUPPORTED_CONTENT_FORMATS:
            print(f"Unsupported Content Format: {int(content_format)} ({content_format.media_type}) -> 4.06 Not Acceptable")
            return aiocoap.Message(code=aiocoap.NOT_ACCEPTABLE)

        print("Reading updated temperature value ...")
        self.temperature_sensor.measure_temperature()
        print(f"Updated Temperature Value: {self.temperature_sensor.temperature_value:.2f}")

        return aiocoap.Message(content_format=content_format, payload=self.build_payload(content_format))
