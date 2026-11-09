# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run coap-put-client [resource_path] [payload]
#
# Send a CoAP PUT request with a plain text payload to a resource of the target server and print the response.
# - uv run coap-put-client demo hello           (string-demo-server): replaces the string value
# - uv run coap-put-client switch false         (smart-object-server): turns OFF the switch actuator

from coap_playground.config.config_manager import ConfigManager
from aiocoap.numbers import ContentFormat
import aiocoap
import asyncio
import logging
import sys

# Configuration variables
default_resource_path = "demo"
default_payload = "demo_string"


async def send_put_request(config_manager: ConfigManager, resource_path: str, payload: str) -> None:

    context = await aiocoap.Context.create_client_context()

    # Build the PUT request: the payload must be an array of bytes, and the Content-Format option
    # tells the server how to interpret it (text/plain)
    target_uri = config_manager.build_server_uri(resource_path)
    request = aiocoap.Message(code=aiocoap.PUT,
                              uri=target_uri,
                              content_format=ContentFormat.TEXT,
                              payload=payload.encode("utf-8"))
    print(f"Sending PUT request to: {target_uri} with payload: {payload}")

    try:
        response = await context.request(request).response
    except Exception as e:
        print(f"Failed to fetch resource: {e}")
    else:
        print(f"Response Code: {response.code}")
        print(f"Payload (string): {response.payload.decode('utf-8')}")
    finally:
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    resource_path = sys.argv[1] if len(sys.argv) > 1 else default_resource_path
    payload = sys.argv[2] if len(sys.argv) > 2 else default_payload

    asyncio.run(send_put_request(config_manager, resource_path, payload))


if __name__ == "__main__":
    main()
