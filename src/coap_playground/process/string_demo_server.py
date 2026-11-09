# For this example we rely on the aiocoap library (0.4.x) - https://github.com/chrysn/aiocoap
# Dependencies are managed with uv. From the project root run: uv run string-demo-server
#
# The server exposes a single resource (/demo) with a string value that supports GET, POST and PUT.
# aiocoap is based on asyncio: the server runs in the event loop and each request is handled
# by the async render_<method>() of the target resource (see the "Asynchronous Model of aiocoap" section of the README).

from coap_playground.config.config_manager import ConfigManager
from coap_playground.resources.string_demo_resource import StringDemoResource
import aiocoap
import aiocoap.resource as resource
import asyncio
import logging

# Configuration variables
resource_path = ["demo"]


async def run_server(config_manager: ConfigManager) -> None:

    # Resource tree creation: the Site is the root of the tree and dispatches each request to the resource
    # registered on the requested path (e.g., coap://127.0.0.1:5683/demo -> ["demo"])
    root = resource.Site()
    root.add_resource(resource_path, StringDemoResource())

    # Create the server context bound to the configured address and UDP port.
    # The method is a coroutine: the server is ready to receive requests when the await returns
    await aiocoap.Context.create_server_context(root, bind=(config_manager.server_bind_host, config_manager.server_port))

    print(f"CoAP Server listening on coap://{config_manager.server_bind_host}:{config_manager.server_port}/{'/'.join(resource_path)}")

    # Keep the server running forever: the requests are served by the event loop while we wait on a Future
    # that is never completed (CTRL+C to stop the process)
    await asyncio.get_running_loop().create_future()


def main() -> None:

    # Log level of aiocoap: INFO shows the main events, DEBUG also shows every received and sent message
    logging.basicConfig(level=logging.INFO)
    # logging.getLogger("coap-server").setLevel(logging.DEBUG)

    # Load the shared configuration (bind address and port of the server) from the config.yaml file
    config_manager = ConfigManager()

    # asyncio.run() creates the event loop, runs the coroutine until it completes and closes the loop
    try:
        asyncio.run(run_server(config_manager))
    except KeyboardInterrupt:
        print("CoAP Server stopped")


if __name__ == "__main__":
    main()
