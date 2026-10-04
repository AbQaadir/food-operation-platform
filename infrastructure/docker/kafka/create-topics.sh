#!/bin/sh
set -e

echo "Waiting for Kafka to be ready..."
/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1
while [ $? -ne 0 ]; do
  sleep 1
  /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1
done

echo "Kafka is ready. Creating required topics with 3 partitions..."

TOPICS="order.created order.confirmed order.cancelled inventory.reserved inventory.rejected inventory.released inventory.low-stock product.updated notifications order.events.DLQ"

for TOPIC in $TOPICS; do
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic "$TOPIC" --partitions 3 --replication-factor 1
  echo "Verified topic: $TOPIC"
done

echo "All Kafka topics created and verified."
