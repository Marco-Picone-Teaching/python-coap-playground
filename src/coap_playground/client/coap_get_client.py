# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run coap-get-client [resource_path]
#
# Send a CoAP GET request to a resource of the target server and print the response.
# The path of the resource can be passed as argument (e.g., uv run coap-get-client temperature),
# otherwise the default_resource_path variable is used.

from coap_playground.config.config_manager import ConfigManager
import aiocoap
import asyncio
import logging
import sys

# Configuration variables
# Change the target resource according to the running server: "demo" (string-demo-server),
# "temperature" (temperature-sensor-server, smart-object-server) or "switch" (smart-object-server)
default_resource_path = "demo"


async def send_get_request(config_manager: ConfigManager, resource_path: str) -> None:

    # Create the client context: it manages the UDP socket, the message ids, the tokens and the retransmissions
    context = await aiocoap.Context.create_client_context()

    # Build the GET request with the complete URI of the resource (e.g., coap://127.0.0.1:5683/demo).
    # The request is Confirmable (CON) by default
    target_uri = config_manager.build_server_uri(resource_path)
    request = aiocoap.Message(code=aiocoap.GET, uri=target_uri)
    print(f"Sending GET request to: {target_uri}")

    try:
        # context.request() sends the request, while awaiting .response waits for the response
        # (managing the retransmissions of the CON message if the ACK is not received)
        response = await context.request(request).response
    except Exception as e:
        print(f"Failed to fetch resource: {e}")
    else:
        # The payload is an array of bytes: decode it to obtain the string representation
        response_string = response.payload.decode("utf-8")
        print(f"Response Code: {response.code}")
        content_format = response.opt.content_format
        if content_format is not None:
            print(f"Content Format: {int(content_format)} ({content_format.media_type})")
        print(f"Payload (bytes): {response.payload!r}")
        print(f"Payload (string): {response_string}")
    finally:
        # Release the resources of the client context (UDP socket)
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    resource_path = sys.argv[1] if len(sys.argv) > 1 else default_resource_path

    asyncio.run(send_get_request(config_manager, resource_path))


if __name__ == "__main__":
    main()
