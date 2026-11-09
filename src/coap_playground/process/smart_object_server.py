# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run smart-object-server
#
# The server emulates an IoT Smart Object with two resources described with the CoRE Link Format (RFC 6690):
# - /temperature: observable temperature sensor (rt="it.unimore.device.sensor.temperature", if="core.s")
# - /switch: switch actuator (rt="it.unimore.device.actuator.switch", if="core.a")
# Both resources return SenML JSON payloads and are listed by the standard /.well-known/core resource,
# allowing a client to discover them without knowing their paths in advance (CoAP Resource Discovery).

from coap_playground.config.config_manager import ConfigManager
from coap_playground.resources.core_switch_actuator_resource import CoreSwitchActuatorResource
from coap_playground.resources.core_temperature_sensor_resource import CoreTemperatureSensorResource
import aiocoap
import aiocoap.resource as resource
import asyncio
import logging

# Configuration variables
device_name = "urn:demo-smartobject-0001"
update_period_s = 5.0


async def run_server(config_manager: ConfigManager) -> None:

    temperature_resource = CoreTemperatureSensorResource(device_name, update_period_s)
    switch_resource = CoreSwitchActuatorResource(device_name)

    # Resource tree creation
    root = resource.Site()

    # Add the /.well-known/core resource to support the standard CoAP Resource Discovery.
    # The WKCResource builds the CoRE Link Format description of all the resources of the Site
    # (get_resources_as_linkheader), using the attributes (rt, if, ct, obs, title) exposed by each resource.
    # impl_info=None removes the link to the aiocoap web site that is added by default
    root.add_resource([".well-known", "core"], resource.WKCResource(root.get_resources_as_linkheader, impl_info=None))
    root.add_resource(["temperature"], temperature_resource)
    root.add_resource(["switch"], switch_resource)

    # Create the server context bound to the configured address and UDP port
    await aiocoap.Context.create_server_context(root, bind=(config_manager.server_bind_host, config_manager.server_port))

    # Start the periodic measurements of the temperature sensor (requires a running event loop)
    temperature_resource.start_measurements()

    print(f"CoAP Smart Object '{device_name}' listening on coap://{config_manager.server_bind_host}:{config_manager.server_port}")
    print(f"Resource Discovery: coap://{config_manager.server_bind_host}:{config_manager.server_port}/.well-known/core")

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
