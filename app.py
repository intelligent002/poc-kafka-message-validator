import json
import os
import sys
from decimal import Decimal
from datetime import datetime, date

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer


# =========================
# JSON SAFE SERIALIZER
# =========================
def json_safe(obj):
    if isinstance(obj, Decimal):
        return str(obj)  # preserve precision

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    return str(obj)

def is_silent_mode() -> bool:
    return os.getenv("SILENT_MODE", "false").lower() in ("1", "true", "yes")

# =========================
# CONFIG: KAFKA
# =========================
def build_kafka_config():
    config = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        "group.id": os.getenv("KAFKA_GROUP_ID", "json-validator-group"),
        "auto.offset.reset": os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        "enable.auto.commit": True,
    }

    protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    config["security.protocol"] = protocol

    if protocol in ("SSL", "SASL_SSL"):
        if os.getenv("KAFKA_SSL_CA_LOCATION"):
            config["ssl.ca.location"] = os.getenv("KAFKA_SSL_CA_LOCATION")

        if os.getenv("KAFKA_SSL_CERT_LOCATION"):
            config["ssl.certificate.location"] = os.getenv("KAFKA_SSL_CERT_LOCATION")

        if os.getenv("KAFKA_SSL_KEY_LOCATION"):
            config["ssl.key.location"] = os.getenv("KAFKA_SSL_KEY_LOCATION")

        if os.getenv("KAFKA_SSL_KEY_PASSWORD"):
            config["ssl.key.password"] = os.getenv("KAFKA_SSL_KEY_PASSWORD")

    if protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
        if os.getenv("KAFKA_SASL_MECHANISM"):
            config["sasl.mechanism"] = os.getenv("KAFKA_SASL_MECHANISM")

        if os.getenv("KAFKA_SASL_USERNAME"):
            config["sasl.username"] = os.getenv("KAFKA_SASL_USERNAME")

        if os.getenv("KAFKA_SASL_PASSWORD"):
            config["sasl.password"] = os.getenv("KAFKA_SASL_PASSWORD")

    if os.getenv("KAFKA_DEBUG"):
        config["debug"] = os.getenv("KAFKA_DEBUG")

    return config


# =========================
# CONFIG: SCHEMA REGISTRY
# =========================
def build_schema_registry():
    url = os.getenv("SCHEMA_REGISTRY_URL")
    if not url:
        return None

    conf = {
        "url": url,
    }

    if os.getenv("SCHEMA_REGISTRY_BASIC_AUTH"):
        conf["basic.auth.user.info"] = os.getenv("SCHEMA_REGISTRY_BASIC_AUTH")

    # SSL (Schema Registry uses HTTP client, limited support)
    if os.getenv("SCHEMA_REGISTRY_SSL_CA_LOCATION"):
        conf["ssl.ca.location"] = os.getenv("SCHEMA_REGISTRY_SSL_CA_LOCATION")

    if os.getenv("SCHEMA_REGISTRY_SSL_CERT_LOCATION"):
        conf["ssl.certificate.location"] = os.getenv("SCHEMA_REGISTRY_SSL_CERT_LOCATION")

    if os.getenv("SCHEMA_REGISTRY_SSL_KEY_LOCATION"):
        conf["ssl.key.location"] = os.getenv("SCHEMA_REGISTRY_SSL_KEY_LOCATION")

    # NOTE:
    # DO NOT include:
    # - ssl.key.password
    # - ssl.endpoint.identification.algorithm

    return SchemaRegistryClient(conf)


# =========================
# DETECTION
# =========================
def is_confluent_avro(raw: bytes) -> bool:
    return len(raw) > 5 and raw[0] == 0


# =========================
# HEX DUMP
# =========================
def hex_dump(data: bytes, width: int = 16):
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]

        hex_part = " ".join(f"{b:02x}" for b in chunk)
        hex_part = hex_part.ljust(width * 3)

        ascii_part = "".join(
            chr(b) if 32 <= b <= 126 else "."
            for b in chunk
        )

        print(f"{offset:08x}  {hex_part}  |{ascii_part}|")


# =========================
# JSON PARSER
# =========================
def try_json(raw: bytes):
    try:
        return json.loads(raw)
    except Exception:
        return None


# =========================
# MAIN
# =========================
def main():
    silent = is_silent_mode()
    topic = os.getenv("KAFKA_TOPIC")
    if not topic:
        raise RuntimeError("KAFKA_TOPIC is required")

    kafka_config = build_kafka_config()
    consumer = Consumer(kafka_config)
    consumer.subscribe([topic])

    sr_client = build_schema_registry()
    avro_deserializer = AvroDeserializer(sr_client) if sr_client else None

    print(f"Listening on topic: {topic}", file=sys.stderr)

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(f"Kafka error: {msg.error()}", file=sys.stderr)
                continue

            raw = msg.value()
            if raw is None:
                continue

            # =========================
            # AVRO PATH
            # =========================
            if is_confluent_avro(raw):
                schema_id = int.from_bytes(raw[1:5], "big")

                print("\n=== AVRO MESSAGE ===")
                print(f"offset={msg.offset()} partition={msg.partition()} schema_id={schema_id}")

                if avro_deserializer:
                    try:
                        decoded = avro_deserializer(raw, None)

                        print("OK (AVRO)")
                        if not silent:
                            print(json.dumps(decoded, ensure_ascii=False, indent=2, default=json_safe))

                    except Exception as e:
                        print("\n=== INVALID AVRO MESSAGE DETECTED ===")
                        print(f"offset={msg.offset()} partition={msg.partition()}")
                        print(f"AVRO decode failed: {e}")
                        hex_dump(raw)
                else:
                    print("Schema Registry not configured")
                    hex_dump(raw)

                print("========================================\n")
                continue

            # =========================
            # JSON PATH
            # =========================
            parsed = try_json(raw)

            if parsed is not None:
                print("OK (JSON)")
                if not silent:
                    print(json.dumps(parsed, ensure_ascii=False, indent=2, default=json_safe))
            else:
                print("\n=== INVALID JSON MESSAGE DETECTED ===")
                print(f"offset={msg.offset()} partition={msg.partition()}")
                hex_dump(raw)
                print("========================================\n")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()