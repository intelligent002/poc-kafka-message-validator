# Kafka JSON / Avro Validator (Hex Debug Tool)

A Kafka consumer for inspecting and validating message payloads.

Supports: - JSON validation - Avro (Confluent wire format)
auto-detection - Schema Registry decoding (optional) - Hex dump for raw
debugging

------------------------------------------------------------------------

## Features

- Automatic format detection (JSON vs Avro)
- Schema Registry integration (optional)
- Full SSL / SASL support for Kafka
- Full SSL support for Schema Registry
- Byte-level hex inspection

------------------------------------------------------------------------

## Build

docker build -t kafka-json-validator .

------------------------------------------------------------------------

## Environment Variables

### Operator Convenience

| Variable    | Required | Description            |
|-------------|----------|------------------------|
| SILENT_MODE | No       | Boolean for less noise |


### Core Kafka

| Variable                | Required | Description                |
|-------------------------|----------|----------------------------|
| KAFKA_BOOTSTRAP_SERVERS | Yes      | Kafka brokers              |
| KAFKA_TOPIC             | Yes      | Topic name                 |
| KAFKA_GROUP_ID          | No       | Consumer group             |
| KAFKA_AUTO_OFFSET_RESET | No       | earliest / latest          |
| KAFKA_SECURITY_PROTOCOL | No       | PLAINTEXT / SSL / SASL_SSL |

### Kafka SSL

| Variable                | Description |
|-------------------------|-------------|
| KAFKA_SSL_CA_LOCATION   | CA cert     |
| KAFKA_SSL_CERT_LOCATION | Client cert |
| KAFKA_SSL_KEY_LOCATION  | Client key  |
| KAFKA_SSL_KEY_PASSWORD  | Optional    |

### Kafka SASL

| Variable             | Description   |
|----------------------|---------------|
| KAFKA_SASL_MECHANISM | SCRAM / PLAIN |
| KAFKA_SASL_USERNAME  | Username      |
| KAFKA_SASL_PASSWORD  | Password      |

### Schema Registry

| Variable                   | Description         |
|----------------------------|---------------------|
| SCHEMA_REGISTRY_URL        | http(s)://host:port |
| SCHEMA_REGISTRY_BASIC_AUTH | user:pass           |

### Schema Registry SSL

| Variable                                              | Description |
|-------------------------------------------------------|-------------|
| SCHEMA_REGISTRY_SSL_CA_LOCATION                       | CA cert     |
| SCHEMA_REGISTRY_SSL_CERT_LOCATION                     | Client cert |
| SCHEMA_REGISTRY_SSL_KEY_LOCATION                      | Client key  |
| SCHEMA_REGISTRY_SSL_KEY_PASSWORD                      | Optional    |
| SCHEMA_REGISTRY_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM | e.g. none   |

------------------------------------------------------------------------

## Behavior

Message Type Action
  ----------------- ----------------------
JSON valid OK (JSON)
JSON invalid Hex dump
Avro + SR Decode + print JSON
Avro without SR Hex dump + schema_id

------------------------------------------------------------------------

## Example: PLAINTEXT

```bash
docker run --rm\
-e KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092 \
-e KAFKA_TOPIC=my-topic \
-e SILENT_MODE=true \
kafka-json-validator
```

------------------------------------------------------------------------

## Example: SSL + Schema Registry

```bash
docker run --rm \
-e KAFKA_BOOTSTRAP_SERVERS=SSL://node-04.intel.r7g.org:9093,SSL://node-05.intel.r7g.org:9093,SSL://node-06.intel.r7g.org:9093 \
-e KAFKA_TOPIC=cdc-mssql-FHIR-EMPLOYEES \
-e KAFKA_SECURITY_PROTOCOL=SSL \
-e KAFKA_SSL_CA_LOCATION=/certs/CA/ca.crt \
-e KAFKA_SSL_CERT_LOCATION=/certs/users/admin/admin.pem \
-e KAFKA_SSL_KEY_LOCATION=/certs/users/admin/admin.key \
-e SCHEMA_REGISTRY_URL=https://node-00.intel.r7g.org:9030 \
-e SCHEMA_REGISTRY_SSL_CA_LOCATION=/certs/CA/ca.crt \
-e SCHEMA_REGISTRY_SSL_CERT_LOCATION=/certs/users/admin/admin.pem \
-e SCHEMA_REGISTRY_SSL_KEY_LOCATION=/certs/users/admin/admin.key \
-e SILENT_MODE=false \
-v /data/cluster/certificates:/certs:ro \
kafka-json-validator
```

------------------------------------------------------------------------

## Output Examples

### JSON

```bash
OK (JSON) offset=102345456 partition=2
```

------------------------------------------------------------------------

### Avro

```bash
OK (AVRO) offset=828234456 partition=9
```

------------------------------------------------------------------------

### Invalid

```bash
=== INVALID AVRO MESSAGE DETECTED ===
offset=828234452 partition=3
00000000 7b 22 6e ... |...|
=====================================
```

------------------------------------------------------------------------

## Notes

- Avro detection is based on Confluent wire format
- Schema Registry is optional but required for decoding
- Tool is designed for CDC / Debezium debugging
- Works with binary payloads and encoding issues
