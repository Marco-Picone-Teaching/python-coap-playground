# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run coap-observe-client [resource_path]
#
# CoAP Observe (RFC 7641): the client registers as observer of a resource by sending a GET request with
# the Observe option set to 0 (register). The server sends the current representation as first response
# and then a notification every time the state of the resource changes. After a fixed number of
# notifications the client cancels the observation.
# Default resource: /temperature-sensor-obs (obs-temperature-sensor-server).
# With the smart-object-server use: uv run coap-observe-client temperature

from coap_playground.config.config_manager import ConfigManager
import aiocoap
import asyncio
import logging
import sys

# Configuration variables
default_resource_path = "temperature-sensor-obs"
notification_limit = 10


async def observe_resource(config_manager: ConfigManager, resource_path: str) -> None:

    context = await aiocoap.Context.create_client_context()

    # Observe option = 0 -> register as observer (1 would mean deregister)
    target_uri = config_manager.build_server_uri(resource_path)
    request = aiocoap.Message(code=aiocoap.GET, uri=target_uri, observe=0)
    print(f"Observing resource: {target_uri}")

    # The request object gives access both to the first response and to the stream of the notifications
    observation_request = context.request(request)

    try:
        # First response: current representation of the resource
        first_response = await observation_request.response
        print(f"First Response: {first_response.code} Observe: {first_response.opt.observe} "
              f"Payload: {first_response.payload.decode('utf-8')}")

        # If the server does not support Observe on the resource, the response has no Observe option
        if first_response.opt.observe is None:
            print("The resource is not observable: no notifications will be received")
            return

        received_notifications = 0

        # Asynchronous iteration over the notifications: each one has an increasing value of the Observe option
        async for notification in observation_request.observation:
            received_notifications += 1
            print(f"Notification {received_notifications}: {notification.code} "
                  f"Observe: {notification.opt.observe} Payload: {notification.payload.decode('utf-8')}")

            if received_notifications == notification_limit:
                # Cancel the observation: the server removes the client from the list of observers
                print("Canceling Observation ...")
                observation_request.observation.cancel()
                break

    except Exception as e:
        print(f"Observation failed: {e}")
    finally:
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    resource_path = sys.argv[1] if len(sys.argv) > 1 else default_resource_path

    try:
        asyncio.run(observe_resource(config_manager, resource_path))
    except KeyboardInterrupt:
        print("Observation stopped")


if __name__ == "__main__":
    main()
