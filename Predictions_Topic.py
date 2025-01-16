from kafka.admin import KafkaAdminClient, NewTopic

# Constants for Kafka configuration
KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "Predictions"  # Name of the unique topic
NUM_PARTITIONS = 5  # Number of partitions
REPLICATION_FACTOR = 1  # Replication factor

# Function to create a topic with 5 partitions
def create_data_stream_topic(admin_client):
    # Create a new topic with the specified number of partitions and replication factor
    new_topic = NewTopic(name=TOPIC_NAME, num_partitions=NUM_PARTITIONS, replication_factor=REPLICATION_FACTOR)
    
    # Create the topic using the admin client
    admin_client.create_topics([new_topic], validate_only=False)
    print(f"Topic created: {TOPIC_NAME} with {NUM_PARTITIONS} partitions.")

# Main function to create the topic
def main():
    # Initialize the Kafka admin client
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
    
    # Create a single topic with 5 partitions
    create_data_stream_topic(admin_client)

if __name__ == "__main__":
    main()

