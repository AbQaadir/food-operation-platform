package com.foodplatform.order.event;

import com.foodplatform.order.service.OrderService;
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

    public OrderChoreographyListener(OrderService orderService) {
        this.orderService = orderService;
    }

    @KafkaListener(topics = "inventory.reserved", groupId = "order-choreography-group")
    public void onInventoryReserved(Map<String, Object> message) {
        try {
            log.info("Received inventory.reserved event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            orderService.confirmOrder(orderId);
        } catch (Exception e) {
            log.error("Failed to process inventory.reserved: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "inventory.rejected", groupId = "order-choreography-group")
    public void onInventoryRejected(Map<String, Object> message) {
        try {
            log.info("Received inventory.rejected event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            String reason = message.get("reason") != null ? message.get("reason").toString() : "Stock allocation failed";
            orderService.rejectOrder(orderId, reason);
        } catch (Exception e) {
            log.error("Failed to process inventory.rejected: {}", e.getMessage());
        }
    }
}
