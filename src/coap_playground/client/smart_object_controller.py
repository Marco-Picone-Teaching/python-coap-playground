# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# and on the LinkHeader library to parse the CoRE Link Format (RFC 6690).
# Dependencies are managed with uv. From the project root run: uv run smart-object-controller
#
# Controller of the CoAP Smart Object (smart-object-server). The controller does not know the paths
# of the resources in advance:
# 1. it discovers the resources through /.well-known/core and looks for the expected Resource Types (rt);
# 2. it observes the temperature sensor (SenML JSON notifications);
# 3. when the temperature is above a limit and the switch is ON, it turns OFF the switch (PUT "false");
# 4. after a delay it turns the switch ON again (PUT "true"), using a separate asyncio task as a timer.

from coap_playground.config.config_manager import ConfigManager
from aiocoap.numbers import ContentFormat
import aiocoap
import asyncio
import json
import link_header
import logging

# Configuration variables
RT_TEMPERATURE_SENSOR = "it.unimore.device.sensor.temperature"
RT_SWITCH_ACTUATOR = "it.unimore.device.actuator.switch"
WELL_KNOWN_CORE_PATH = "/.well-known/core"
TEMPERATURE_LIMIT = 37.0
SWITCH_ON_DELAY_S = 10.0
NOTIFICATION_LIMIT = 50


async def discover_resources(context: aiocoap.Context, config_manager: ConfigManager) -> dict[str, str]:
    """ Discover the resources of the Smart Object and return a dictionary {resource_type: path} """

    request = aiocoap.Message(code=aiocoap.GET, uri=config_manager.build_server_uri(WELL_KNOWN_CORE_PATH))
    response = await context.request(request).response

    resource_paths: dict[str, str] = {}
    for link in link_header.parse(response.payload.decode("utf-8")).links:
        for attribute_name, attribute_value in link.attr_pairs:
            if attribute_name == "rt":
                resource_paths[attribute_value] = link.href

    return resource_paths


def read_senml_value(payload: bytes) -> float | bool | None:
    """ Read the value of the first SenML record: numeric value (v) or boolean value (vb) """

    records = json.loads(payload.decode("utf-8"))
    if len(records) == 0:
        return None
    if "v" in records[0]:
        return float(records[0]["v"])
    if "vb" in records[0]:
        return bool(records[0]["vb"])
    return None


async def read_switch_status(context: aiocoap.Context, switch_uri: str) -> bool | None:
    """ Read the current status of the switch (GET with SenML JSON response) """

    response = await context.request(aiocoap.Message(code=aiocoap.GET, uri=switch_uri)).response
    value = read_senml_value(response.payload)
    return value if isinstance(value, bool) else None


async def set_switch_status(context: aiocoap.Context, switch_uri: str, status: bool) -> None:
    """ Set the status of the switch with a PUT request ("true" / "false" plain text payload) """

    request = aiocoap.Message(code=aiocoap.PUT,
                              uri=switch_uri,
                              content_format=ContentFormat.TEXT,
                              payload=str(status).lower().encode("utf-8"))
    response = await context.request(request).response
    print(f"PUT {switch_uri} -> {str(status).lower()} Response Code: {response.code}")


async def switch_on_after_delay(context: aiocoap.Context, switch_uri: str) -> None:
    """ Timer: wait for a delay and then turn ON the switch """

    await asyncio.sleep(SWITCH_ON_DELAY_S)
    print(f"Timer expired after {SWITCH_ON_DELAY_S} seconds -> Switch ON")
    await set_switch_status(context, switch_uri, True)


async def run_controller(config_manager: ConfigManager) -> None:

    context = await aiocoap.Context.create_client_context()

    try:
        # 1. Resource Discovery and validation of the Resource Types
        resource_paths = await discover_resources(context, config_manager)
        print(f"Discovered Resource Types: {resource_paths}")

        if RT_TEMPERATURE_SENSOR not in resource_paths or RT_SWITCH_ACTUATOR not in resource_paths:
            print("Error: the target device does not expose the required resources !")
            return

        temperature_uri = config_manager.build_server_uri(resource_paths[RT_TEMPERATURE_SENSOR])
        switch_uri = config_manager.build_server_uri(resource_paths[RT_SWITCH_ACTUATOR])
        print(f"Temperature Sensor: {temperature_uri}")
        print(f"Switch Actuator: {switch_uri}")

        # 2. Observe the temperature sensor
        observation_request = context.request(aiocoap.Message(code=aiocoap.GET, uri=temperature_uri, observe=0))
        first_response = await observation_request.response
        print(f"Current Temperature: {read_senml_value(first_response.payload)}")

        # Reference to the timer task (to avoid starting more timers at the same time)
        switch_on_task: asyncio.Task[None] | None = None
        received_notifications = 0

        async for notification in observation_request.observation:
            received_notifications += 1
            temperature_value = read_senml_value(notification.payload)
            print(f"Notification {received_notifications} - Temperature: {temperature_value}")

            # 3. Check the temperature limit (the value could be None or a boolean if the payload is not the expected one)
            if isinstance(temperature_value, float) and temperature_value > TEMPERATURE_LIMIT:
                switch_status = await read_switch_status(context, switch_uri)
                if switch_status:
                    print(f"Temperature above the limit ({TEMPERATURE_LIMIT}) -> Switch OFF")
                    await set_switch_status(context, switch_uri, False)

                    # 4. Start the timer in a separate task: the loop keeps receiving the notifications in the meantime
                    if switch_on_task is None or switch_on_task.done():
                        switch_on_task = asyncio.create_task(switch_on_after_delay(context, switch_uri))

            if received_notifications == NOTIFICATION_LIMIT:
                print("Canceling Observation ...")
                observation_request.observation.cancel()
                break

    except Exception as e:
        print(f"Controller error: {e}")
    finally:
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    try:
        asyncio.run(run_controller(config_manager))
    except KeyboardInterrupt:
        print("Controller stopped")


if __name__ == "__main__":
    main()
