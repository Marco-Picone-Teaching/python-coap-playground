# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run temperature-sensor-server
#
# The server exposes a read-only temperature sensor resource (/temperature) that supports
# Content Format Negotiation: the client selects the representation with the Accept option
# (application/json, text/plain, application/senml+json or application/senml+cbor).

from coap_playground.config.config_manager import ConfigManager
from coap_playground.resources.temperature_sensor_resource import TemperatureSensorResource
import aiocoap
import aiocoap.resource as resource
import asyncio
import logging

# Configuration variables
device_name = "urn:demo-temperature-sensor-0001"
resource_path = ["temperature"]


async def run_server(config_manager: ConfigManager) -> None:

    # Resource tree creation
    root = resource.Site()
    root.add_resource(resource_path, TemperatureSensorResource(device_name))

    # Create the server context bound to the configured address and UDP port
    await aiocoap.Context.create_server_context(root, bind=(config_manager.server_bind_host, config_manager.server_port))

    print(f"CoAP Server listening on coap://{config_manager.server_bind_host}:{config_manager.server_port}/{'/'.join(resource_path)}")

    # Keep the server running forever (CTRL+C to stop the process)
    await asyncio.get_running_loop().create_future()


def main() -> None:

    logging.basicConfig(level=logging.INFO)
    # logging.getLogger("coap-server").setLevel(logging.DEBUG)

    # Load the shared configuration (bind address and port of the server) from the config.yaml file
    config_manager = ConfigManager()

    try:
        asyncio.run(run_server(config_manager))
    except KeyboardInterrupt:
        print("CoAP Server stopped")


if __name__ == "__main__":
    main()
