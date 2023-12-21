from confluent_kafka import Consumer, KafkaException
import json
import pysolr

SOLR_URL = "http://localhost:8983/solr/orderCollection"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"  # Kafka bootstrap servers

# Create a Solr client
solr = pysolr.Solr(SOLR_URL, timeout=10)

# Create a Kafka consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'badge_listener_group',
    'auto.offset.reset': 'earliest',
}


def process_message(message):
    try:
        # Assuming the Kafka message contains a JSON payload with user_id and badge details
        payload = json.loads(message.value().decode('utf-8'))
        user_id = payload['userId']
        print(f"Payload: {payload}")
        result = solr.search(f"userId:{payload['userId']}")
        user_document = result.docs[0] if result.docs else None

        # Update the "achieved" field in the user document

        # Submit the updated document for indexing
        solr.add([
            {
                "userId": payload['userId'],
                "orderId": payload['orderId'],
                "discountAvailed": payload['discountAvailed'],
                "orderDate": payload['orderDate'],
                "savingPercentage": payload['savingPercentage']
            }
        ])

        # Commit the changes to Solr
        solr.commit()

    except Exception as e:
        print(f"Error processing Kafka message: {e}")


# Set up the Kafka consumer
consumer = Consumer(consumer_config)

# Subscribe to the Kafka topic
consumer.subscribe(['com.gdn.order.details.topic'])

# Start listening for messages
try:
    while True:
        msg = consumer.poll(timeout=1000)  # Adjust the timeout as needed

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaException.args:
                continue
            else:
                print(f"Error: {msg.error()}")
                break

        process_message(msg)

except KeyboardInterrupt:
    pass

finally:
    consumer.close()
