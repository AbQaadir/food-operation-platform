package com.foodplatform.order.event;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.service.OrderService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Component
public class OrderChoreographyListener {

    private static final Logger log = LoggerFactory.getLogger(OrderChoreographyListener.class);

    private final OrderService orderService;
    private final ObjectMapper objectMapper;

    public OrderChoreographyListener(OrderService orderService, ObjectMapper objectMapper) {
        this.orderService = orderService;
        this.objectMapper = objectMapper;
    }

    @KafkaListener(topics = "inventory.reserved", groupId = "order-choreography-group")
    public void onInventoryReserved(ConsumerRecord<String, Object> record) {
        try {
            Map<String, Object> message = extractMap(record.value());
            log.info("Received inventory.reserved event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            orderService.confirmOrder(orderId);
        } catch (Exception e) {
            log.error("Failed to process inventory.reserved: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "inventory.rejected", groupId = "order-choreography-group")
    public void onInventoryRejected(ConsumerRecord<String, Object> record) {
        try {
            Map<String, Object> message = extractMap(record.value());
            log.info("Received inventory.rejected event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            String reason = message.get("reason") != null ? message.get("reason").toString() : "Stock allocation failed";
            orderService.rejectOrder(orderId, reason);
        } catch (Exception e) {
            log.error("Failed to process inventory.rejected: {}", e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractMap(Object value) throws Exception {
        if (value instanceof Map<?, ?> m) {
            return (Map<String, Object>) m;
        } else if (value instanceof String s) {
            return objectMapper.readValue(s, Map.class);
        } else if (value instanceof byte[] b) {
            return objectMapper.readValue(b, Map.class);
        }
        return objectMapper.convertValue(value, Map.class);
    }
}
