# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# and on the LinkHeader library to parse the CoRE Link Format (RFC 6690).
# Dependencies are managed with uv. From the project root run: uv run coap-discovery-client
#
# CoAP Resource Discovery: the client sends a GET request to the standard /.well-known/core resource
# of the smart-object-server and parses the CoRE Link Format response (application/link-format),
# printing the path (href) and the attributes (rt, if, ct, obs, title) of each resource.
# The optional query parameter (e.g., "rt=it.unimore.device.sensor.temperature") filters the resources.

from coap_playground.config.config_manager import ConfigManager
import aiocoap
import asyncio
import link_header
import logging
import sys

# Configuration variables
well_known_core_path = "/.well-known/core"


async def discover_resources(config_manager: ConfigManager, query: str | None) -> None:

    context = await aiocoap.Context.create_client_context()

    # Build the discovery URI, with the optional filter as query string (e.g., /.well-known/core?if=core.s)
    target_uri = config_manager.build_server_uri(well_known_core_path)
    if query is not None:
        target_uri = f"{target_uri}?{query}"

    request = aiocoap.Message(code=aiocoap.GET, uri=target_uri)
    print(f"Sending Discovery request to: {target_uri}")

    try:
        response = await context.request(request).response
    except Exception as e:
        print(f"Failed to fetch resource: {e}")
    else:
        response_string = response.payload.decode("utf-8")
        print(f"Response Code: {response.code}")
        print(f"CoRE Link Format: {response_string}\n")

        # Parse the CoRE Link Format: each link has an href (the path of the resource)
        # and a list of (name, value) attribute pairs
        links = link_header.parse(response_string)
        for link in links.links:
            print(f"Resource: {link.href}")
            for attribute_name, attribute_value in link.attr_pairs:
                print(f"\t{attribute_name}: {attribute_value}")
    finally:
        await context.shutdown()


def main() -> None:

    logging.basicConfig(level=logging.INFO)

    # Load the shared configuration (target server host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Optional filter passed as argument (e.g., uv run coap-discovery-client rt=it.unimore.device.actuator.switch)
    query = sys.argv[1] if len(sys.argv) > 1 else None

    asyncio.run(discover_resources(config_manager, query))


if __name__ == "__main__":
    main()
