import pika
import json
import time
import sys
from prometheus_client import Counter, start_http_server

NOTIFICATIONS_SENT = Counter(
    'notifications_sent_total',
    'Total number of notifications sent'
)

def callback(ch, method, properties, body):
    print(f" [x] Received booking notification: {body}")

    time.sleep(1)
    print(" [x] Notification sent successfully!")

def main():
    start_http_server(8000)
    print(" [*] Metrics server started on :8000")

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()
            channel.queue_declare(queue='booking_notifications')
            channel.basic_consume(queue='booking_notifications', on_message_callback=callback, auto_ack=True)
            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not ready, waiting 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print(' [!] Interrupted')
            sys.exit(0)

if __name__ == "__main__":
    main()