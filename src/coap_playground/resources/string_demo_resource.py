import random
import string

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat


def generate_random_string(length: int) -> str:
    """ Generate a random string of lowercase letters with the given length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


class StringDemoResource(resource.Resource):
    """ Example of a simple String based resource which supports the GET, POST and PUT methods """

    def __init__(self) -> None:
        """ Constructor for StringDemoResource class """
        super().__init__()

        # Initial value of the resource
        self.string_value: str = generate_random_string(10)

    async def render_get(self, request: aiocoap.Message) -> aiocoap.Message:
        """ GET: return the current value of the resource as plain text """

        print("GET Request Received ...")

        # The response code is not specified: aiocoap uses 2.05 Content as default for GET requests
        return aiocoap.Message(content_format=ContentFormat.TEXT, payload=self.string_value.encode("utf-8"))

    async def render_post(self, request: aiocoap.Message) -> aiocoap.Message:
        """ POST: generate a new random value and return it """

        self.string_value = generate_random_string(10)
        print(f"POST Request Received - New Random String generated: {self.string_value}")

        # The value of the existing resource has been changed: 2.04 Changed
        # (2.01 Created should be used if the POST creates a new resource)
        return aiocoap.Message(code=aiocoap.CHANGED,
                               content_format=ContentFormat.TEXT,
                               payload=self.string_value.encode("utf-8"))

    async def render_put(self, request: aiocoap.Message) -> aiocoap.Message:
        """ PUT: replace the value of the resource with the received payload """

        print(f"PUT Request Received - Byte payload: {request.payload!r}")

        # The payload of a CoAP message is an array of bytes that has to be decoded
        payload_string = request.payload.decode("utf-8")
        print(f"PUT String payload: {payload_string}")

        self.string_value = payload_string

        return aiocoap.Message(code=aiocoap.CHANGED,
                               content_format=ContentFormat.TEXT,
                               payload=self.string_value.encode("utf-8"))
