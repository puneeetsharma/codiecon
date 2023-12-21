from confluent_kafka import Consumer, KafkaException
import json
import pysolr

SOLR_URL = "http://localhost:8983/solr/userCollection"  # Update with your Solr URL
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"  # Update with your Kafka bootstrap servers

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
        user_id = payload['user_id']
        badge_name = payload['badge_name']
        print(f"Payload: {payload}")
        # Fetch the existing badges from Solr
        # existing_badges = solr.search(f"userId:{user_id}")['docs'][0].get('achieved_badges', [])
        # print(f"Existing Badges: {existing_badges}")
        # # Add the new badge to the list
        # existing_badges.append(badge_name)

        # Update the Solr document with the new badges
        # solr.update([{'userId': user_id, 'achieved_badges': existing_badges}])
        # Fetch the existing user document from Solr
        result = solr.search(f"userId:{payload['user_id']}")
        user_document = result.docs[0] if result.docs else None

        # Update the "achieved" field in the user document
        if user_document:
            achieved_badges = user_document.get('achieved', [])
            achieved_badges.append(payload['badge_name'])
            url = user_document.get('url')

            # Submit the updated document for indexing
            solr.add([
                {
                    "userId": payload['user_id'],
                    "achieved": achieved_badges,
                    "id": payload['id'],
                    "progress": payload['progress'],
                    "url": url
                }
            ])

            # Commit the changes to Solr
            solr.commit()

    except Exception as e:
        print(f"Error processing Kafka message: {e}")


# Set up the Kafka consumer
consumer = Consumer(consumer_config)

# Subscribe to the Kafka topic
consumer.subscribe(['com.gdn.user_badge_topic'])

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
