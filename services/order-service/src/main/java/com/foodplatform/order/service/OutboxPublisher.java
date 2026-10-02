package com.foodplatform.order.service;

import com.foodplatform.order.domain.OutboxEvent;
import com.foodplatform.order.repository.OutboxEventRepository;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.util.List;

@Service
public class OutboxPublisher {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisher.class);

    private final OutboxEventRepository outboxEventRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public OutboxPublisher(OutboxEventRepository outboxEventRepository,
                           @Autowired(required = false) KafkaTemplate<String, Object> kafkaTemplate) {
        this.outboxEventRepository = outboxEventRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelay = 500)
    @Transactional
    public void publishOutboxEvents() {
        if (kafkaTemplate == null) return;

        List<OutboxEvent> unprocessed = outboxEventRepository.findByProcessedAtIsNullOrderByCreatedAtAsc(PageRequest.of(0, 50));
        for (OutboxEvent event : unprocessed) {
            try {
                ProducerRecord<String, Object> record =
                        new ProducerRecord<>(event.getType(), event.getAggregateId(), event.getPayload());
                record.headers().add("eventId", event.getId().toString().getBytes(StandardCharsets.UTF_8));
                record.headers().add("correlationId", event.getId().toString().getBytes(StandardCharsets.UTF_8));
                record.headers().add("producer", "order-service".getBytes(StandardCharsets.UTF_8));
                kafkaTemplate.send(record).get();
                event.markProcessed();
                outboxEventRepository.save(event);
                log.info("Published outbox event {} for {} to topic {}", event.getId(), event.getAggregateId(), event.getType());
            } catch (Exception e) {
                log.warn("Failed to publish outbox event {}: {}", event.getId(), e.getMessage());
                event.incrementRetry();
                outboxEventRepository.save(event);
            }
        }
    }
}
