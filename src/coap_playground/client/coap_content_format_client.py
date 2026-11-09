# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run coap-content-format-client
#
# Content Format Negotiation: the client sends a sequence of GET requests to the same resource (/temperature
# of the temperature-sensor-server), each one with a different value of the Accept option, and prints how
# the representation (and its size in bytes) changes. The last request asks for an unsupported format
# (application/xml) and receives 4.06 Not Acceptable.

from coap_playground.config.config_manager import ConfigManager
from aiocoap.numbers import ContentFormat
import aiocoap
import asyncio
import cbor2
import logging

# Configuration variables
resource_path = "temperature"

# Requested formats (Accept option): None means that the option is not sent and the server uses its default
requested_formats: list[ContentFormat | None] = [
    None,
    ContentFormat.JSON,                                         # application/json (50)
    ContentFormat.TEXT,                                         # text/plain (0)
    ContentFormat.by_media_type("application/senml+json"),      # application/senml+json (110)
    ContentFormat.by_media_type("application/senml+cbor"),      # application/senml+cbor (112)
    ContentFormat.by_media_type("application/xml"),             # application/xml (41) -> not supported
]


def format_name(content_format: ContentFormat | None) -> str:
    """ Return a readable description of a Content-Format (e.g., "110 (application/senml+json)") """
    if content_format is None:
        return "None"
    return f"{int(content_format)} ({content_format.media_type})"


def decode_payload(response: aiocoap.Message) -> str:
    """ Return a printable version of the payload according to its Content-Format """

    content_format = response.opt.content_format

    # CBOR is a binary format: it can not be decoded as a UTF-8 string, so we decode it with the cbor2 library
    if content_format is not None and content_format.media_type == "application/senml+cbor":
        return f"(decoded CBOR) {cbor2.loads(response.payload)}"

    return response.payload.decode("utf-8")


async def run_negotiation(config_manager: ConfigManager) -> None:

    context = await aiocoap.Context.create_client_context()
    target_uri = config_manager.build_server_uri(resource_path)

    try:
        for requested_format in requested_formats:

            # The Accept option is set only if a format is requested
            request = aiocoap.Message(code=aiocoap.GET, uri=target_uri)
            if requested_format is not None:
                request.opt.accept = requested_format

            print("\n##################################")
            print(f"GET {target_uri} - Accept: {format_name(requested_format)}")

            try:
                response = await context.request(request).response
            except Exception as e:
                print(f"Failed to fetch resource: {e}")
                continue

            print(f"Response Code: {response.code}")

            if response.code.is_successful():
                print(f"Content Format: {format_name(response.opt.content_format)}")
                print(f"Payload Size: {len(response.payload)} bytes")
                print(f"Payload: {decode_payload(response)}")
    finally:
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    asyncio.run(run_negotiation(config_manager))


if __name__ == "__main__":
    main()
