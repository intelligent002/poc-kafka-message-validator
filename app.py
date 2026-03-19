import json
import os
import sys
from confluent_kafka import Consumer


# =========================
# CONFIG
# =========================
def build_kafka_config():
    config = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "group.id": os.getenv("KAFKA_GROUP_ID", "json-validator-group"),
        "auto.offset.reset": os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        "enable.auto.commit": True,
    }

    security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL")

    if security_protocol:
        config["security.protocol"] = security_protocol

    # SSL config (optional)
    if security_protocol in ("SSL", "SASL_SSL"):
        config.update({
            "ssl.ca.location": os.getenv("KAFKA_SSL_CA_LOCATION"),
            "ssl.certificate.location": os.getenv("KAFKA_SSL_CERT_LOCATION"),
            "ssl.key.location": os.getenv("KAFKA_SSL_KEY_LOCATION"),
        })

    # SASL config (optional)
    if security_protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
        config.update({
            "sasl.mechanism": os.getenv("KAFKA_SASL_MECHANISM"),
            "sasl.username": os.getenv("KAFKA_SASL_USERNAME"),
            "sasl.password": os.getenv("KAFKA_SASL_PASSWORD"),
        })

    return config


TOPIC = os.getenv("KAFKA_TOPIC", "test-topic")


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
# JSON VALIDATION
# =========================
def is_valid_json(raw: bytes) -> bool:
    try:
        json.loads(raw)
        return True
    except Exception:
        return False


# =========================
# MAIN
# =========================
def main():
    config = build_kafka_config()

    consumer = Consumer(config)
    consumer.subscribe([TOPIC])

    print(f"Listening on topic: {TOPIC}", file=sys.stderr)
    print(f"Kafka config: {config}", file=sys.stderr)

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

            if is_valid_json(raw):
                print("OK")
            else:
                print("\n=== INVALID MESSAGE ===")
                print(f"offset={msg.offset()} partition={msg.partition()}")
                hex_dump(raw)
                print("=======================\n")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()