# Kafka JSON Validator (Hex Debug Mode)

A lightweight Kafka consumer that:

- Reads messages from a topic
- Validates whether payload is valid JSON
- Prints:
    - OK → for valid JSON
    - Hex dump + metadata → for invalid messages

Designed for CDC debugging, encoding issues, and payload forensics.

---

## Features

- Byte-level inspection (hex + ASCII view)
- Works on raw Kafka bytes (no encoding assumptions)
- Env-driven configuration
- Supports PLAINTEXT, SSL (mTLS), SASL
- Dockerized and stateless

---

## Environment Variables

| Variable                | Required | Default              | Description                |
|-------------------------|----------|----------------------|----------------------------|
| KAFKA_BOOTSTRAP_SERVERS | Yes      | —                    | Kafka bootstrap servers    |
| KAFKA_TOPIC             | Yes      | —                    | Topic to consume           |
| KAFKA_GROUP_ID          | No       | json-validator-group | Consumer group             |
| KAFKA_AUTO_OFFSET_RESET | No       | earliest             | earliest / latest          |
| KAFKA_SECURITY_PROTOCOL | No       | PLAINTEXT            | PLAINTEXT / SSL / SASL_SSL |

### SSL

| Variable                | Description           |
|-------------------------|-----------------------|
| KAFKA_SSL_CA_LOCATION   | CA certificate        |
| KAFKA_SSL_CERT_LOCATION | Client cert           |
| KAFKA_SSL_KEY_LOCATION  | Client key            |
| KAFKA_SSL_KEY_PASSWORD  | Optional key password |

### SASL

| Variable             | Description    |
|----------------------|----------------|
| KAFKA_SASL_MECHANISM | Auth mechanism |
| KAFKA_SASL_USERNAME  | Username       |
| KAFKA_SASL_PASSWORD  | Password       |

---

## Example: PLAINTEXT

```bash
docker run --rm \
-e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 \
-e KAFKA_TOPIC=my-topic \
kafka-json-validator
```

---

## Example: SSL

```bash
docker run --rm \
-e KAFKA_BOOTSTRAP_SERVERS=broker:9093 \
-e KAFKA_TOPIC=my-topic \
-e KAFKA_SECURITY_PROTOCOL=SSL \
-e KAFKA_SSL_CA_LOCATION=/certs/ca.pem \
-e KAFKA_SSL_CERT_LOCATION=/certs/client.pem \
-e KAFKA_SSL_KEY_LOCATION=/certs/client.key \
-v $(pwd)/certs:/certs:ro \
kafka-json-validator
```

---

## Output

```
Valid:
offset=123 partition=0 - OK

Invalid:
=== INVALID MESSAGE DETECTED ===
offset=123 partition=0
00000000 7b 22 6e ... |...|
================================
```

---

## Notes

Useful for debugging:

- Debezium / CDC pipelines
- Encoding issues (UTF-8 / Hebrew corruption)
- Broken JSON payloads
