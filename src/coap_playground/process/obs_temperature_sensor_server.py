# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run obs-temperature-sensor-server
#
# The server exposes an Observable temperature sensor resource (/temperature-sensor-obs, RFC 7641).
# A background asyncio task periodically measures a new value and notifies all the registered observers.

from coap_playground.config.config_manager import ConfigManager
from coap_playground.resources.obs_temperature_sensor_resource import ObsTemperatureSensorResource
import aiocoap
import aiocoap.resource as resource
import asyncio
import logging

# Configuration variables
resource_path = ["temperature-sensor-obs"]
update_period_s = 5.0


async def run_server(config_manager: ConfigManager) -> None:

    # Create the observable resource
    temperature_resource = ObsTemperatureSensorResource(update_period_s)

    # Resource tree creation
    root = resource.Site()
    root.add_resource(resource_path, temperature_resource)

    # Create the server context bound to the configured address and UDP port
    await aiocoap.Context.create_server_context(root, bind=(config_manager.server_bind_host, config_manager.server_port))

    # Start the periodic measurements. It must be done here, since asyncio.create_task() requires a running event loop
    temperature_resource.start_measurements()

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
