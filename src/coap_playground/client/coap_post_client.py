# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run coap-post-client [resource_path]
#
# Send a CoAP POST request (without payload) to a resource of the target server and print the response.
# - /demo (string-demo-server): generates a new random string
# - /switch (smart-object-server): toggles the status of the switch actuator

from coap_playground.config.config_manager import ConfigManager
import aiocoap
import asyncio
import logging
import sys

# Configuration variables
default_resource_path = "demo"


async def send_post_request(config_manager: ConfigManager, resource_path: str) -> None:

    context = await aiocoap.Context.create_client_context()

    # Build the POST request without payload
    target_uri = config_manager.build_server_uri(resource_path)
    request = aiocoap.Message(code=aiocoap.POST, uri=target_uri)
    print(f"Sending POST request to: {target_uri}")

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

    asyncio.run(send_post_request(config_manager, resource_path))


if __name__ == "__main__":
    main()
