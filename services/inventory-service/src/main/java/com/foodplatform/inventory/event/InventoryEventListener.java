package com.foodplatform.inventory.event;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.inventory.dto.OrderItemRequest;
import com.foodplatform.inventory.dto.ReleaseStockRequest;
import com.foodplatform.inventory.dto.ReserveStockRequest;
import com.foodplatform.inventory.service.InventoryService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Component
public class InventoryEventListener {

    private static final Logger log = LoggerFactory.getLogger(InventoryEventListener.class);

    private final InventoryService inventoryService;
    private final ObjectMapper objectMapper;

    public InventoryEventListener(InventoryService inventoryService, ObjectMapper objectMapper) {
        this.inventoryService = inventoryService;
        this.objectMapper = objectMapper;
    }

    @KafkaListener(topics = "order.created", groupId = "inventory-service-group")
    public void handleOrderCreated(ConsumerRecord<String, Object> record) {
        try {
            Map<String, Object> message = extractMap(record.value());
            log.info("Received order.created event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> items = (List<Map<String, Object>>) message.get("items");

            if (items != null && !items.isEmpty()) {
                List<OrderItemRequest> orderItems = items.stream().map(i -> new OrderItemRequest(
                        UUID.fromString(i.get("productId").toString()),
                        Integer.parseInt(i.get("qty").toString())
                )).toList();

                inventoryService.reserveStock(new ReserveStockRequest(orderId, orderItems));
            }
        } catch (Exception e) {
            log.warn("Failed to process order.created in inventory-service: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "order.cancelled", groupId = "inventory-service-group")
    public void handleOrderCancelled(ConsumerRecord<String, Object> record) {
        try {
            Map<String, Object> message = extractMap(record.value());
            log.info("Received order.cancelled event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            inventoryService.releaseStock(new ReleaseStockRequest(orderId));
        } catch (Exception e) {
            log.warn("Failed to process order.cancelled in inventory-service: {}", e.getMessage());
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
