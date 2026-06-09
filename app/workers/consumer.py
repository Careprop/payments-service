from faststream import FastStream

from app.messaging.broker import broker

import app.messaging.consumer
import app.messaging.retry_consumer
import app.messaging.dlq_consumer


app = FastStream(broker)
