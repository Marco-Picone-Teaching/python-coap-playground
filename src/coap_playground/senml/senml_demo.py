# For this example we rely on the kpn-senml library - https://github.com/kpn-iot/senml-python-library
# Dependencies are managed with uv. From the project root run: uv run senml-demo
#
# SenML (Sensor Measurement Lists, RFC 8428) is a standard data model to represent sensor measurements
# and device parameters. A SenML Pack is a list of Records, and each Record can define "base" fields
# (bn, bt, bu, bv, bs) that apply to all the following Records. The same Pack can be serialized
# in JSON (application/senml+json, Content-Format 110) or in CBOR (application/senml+cbor, Content-Format 112).
# The demo does not require a running CoAP server.

from kpn_senml import SenmlPack, SenmlRecord, SenmlUnits
import cbor2
import json
import time

# Configuration variables
device_name = "urn:demo-smartobject-0001:"


def build_senml_pack() -> SenmlPack:
    """ Build a SenML Pack with two Records describing different types of values """

    # The name of the Pack becomes the Base Name (bn) of the first Record:
    # the full name of each Record is bn + n (e.g., urn:demo-smartobject-0001:temperature)
    pack = SenmlPack(device_name)

    # Numeric value (v) with a unit (u) from the SenML Units registry ("Cel" = degrees Celsius)
    temperature = SenmlRecord("temperature", unit=SenmlUnits.SENML_UNIT_DEGREES_CELSIUS, value=23.5)

    # Boolean value (vb)
    door_position = SenmlRecord("door-open", value=False)

    # Note: SenML also defines string values (vs), but kpn-senml 1.0.1 raises a NameError ("basestring")
    # with string values on Python 3, so they are not used in the playground

    pack.add(temperature)
    pack.add(door_position)

    # Base Time (bt): absolute time of the Pack (Unix time in seconds). kpn-senml expects absolute times on the
    # Records and serializes them relative to the Base Time: a measurement taken 5 seconds after bt has t = 5
    now = int(time.time())
    pack.base_time = now
    temperature.time = now + 5

    return pack


def on_senml_record(record: SenmlRecord, **kwargs) -> None:
    """ Callback called by kpn-senml for each Record found while parsing a Pack """
    print(f"\tParsed Record -> name: {record.name} value: {record.value}")


def main() -> None:

    pack = build_senml_pack()

    # JSON serialization: the field names are short labels (n, v, vb, vs, u, t, bn, bt, ...)
    json_payload = pack.to_json()
    print("SenML JSON (application/senml+json):")
    print(json.dumps(json.loads(json_payload), indent=2))
    print(f"Size: {len(json_payload.encode('utf-8'))} bytes\n")

    # CBOR serialization: binary encoding where the labels are replaced by integer keys (e.g., n -> 0, v -> 2)
    cbor_payload = pack.to_cbor()
    print("SenML CBOR (application/senml+cbor):")
    print(f"Bytes: {cbor_payload.hex(' ')}")
    print(f"Size: {len(cbor_payload)} bytes")
    print(f"Decoded with cbor2: {cbor2.loads(cbor_payload)}\n")

    # De-serialization: the callback passed to the Pack is called for each Record found in the payload
    # (kpn-senml uses this mechanism to deliver the commands received by an actuator)
    print("Parsing the SenML JSON payload:")
    received_pack = SenmlPack(device_name, on_senml_record)
    received_pack.from_json(json_payload)

    print("Parsing the SenML CBOR payload:")
    received_cbor_pack = SenmlPack(device_name, on_senml_record)
    received_cbor_pack.from_cbor(cbor_payload)


if __name__ == "__main__":
    main()
