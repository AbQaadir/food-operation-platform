package com.foodplatform.order.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.client.ProductClient;
import com.foodplatform.order.domain.*;
import com.foodplatform.order.dto.*;
import com.foodplatform.order.exception.InvalidOrderStateException;
import com.foodplatform.order.exception.ResourceNotFoundException;
import com.foodplatform.order.repository.OrderRepository;
import com.foodplatform.order.repository.OutboxEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository orderRepository;
    private final OutboxEventRepository outboxEventRepository;
    private final ProductClient productClient;
    private final ObjectMapper objectMapper;

    public OrderService(OrderRepository orderRepository,
                        OutboxEventRepository outboxEventRepository,
                        ProductClient productClient,
                        ObjectMapper objectMapper) {
        this.orderRepository = orderRepository;
        this.outboxEventRepository = outboxEventRepository;
        this.productClient = productClient;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
    public OrderDto getOrderById(UUID id) {
        return orderRepository.findById(id)
                .map(this::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + id));
    }

    @Transactional(readOnly = true)
    public PagedResponse<OrderDto> getOrders(UUID customerId, OrderStatus status, Pageable pageable) {
        Page<Order> page;
        if (customerId != null && status != null) {
            page = orderRepository.findByCustomerIdAndStatus(customerId, status, pageable);
        } else if (customerId != null) {
            page = orderRepository.findByCustomerId(customerId, pageable);
        } else if (status != null) {
            page = orderRepository.findByStatus(status, pageable);
        } else {
            page = orderRepository.findAll(pageable);
        }
        return PagedResponse.from(page.map(this::toDto));
    }

    /**
     * Transactional Outbox Pattern:
     * Saves the Order and creates the OutboxEvent within the same ACID database transaction!
     */
    @Transactional
    public OrderDto createOrder(CreateOrderRequest req) {
        UUID orderId = UUID.randomUUID();
        BigDecimal totalAmount = BigDecimal.ZERO;

        List<OrderItem> items = new ArrayList<>();
        List<Map<String, Object>> eventItems = new ArrayList<>();

        for (CreateOrderItemRequest itemReq : req.items()) {
            ProductClient.ProductInfo pInfo = productClient.fetchProduct(itemReq.productId());
            String sku = itemReq.sku() != null ? itemReq.sku() : pInfo.sku();
            String name = itemReq.productName() != null ? itemReq.productName() : pInfo.name();
            BigDecimal unitPrice = itemReq.unitPrice() != null ? itemReq.unitPrice() : pInfo.price();

            BigDecimal subtotal = unitPrice.multiply(BigDecimal.valueOf(itemReq.qty()));
            totalAmount = totalAmount.add(subtotal);

            OrderItem orderItem = new OrderItem(UUID.randomUUID(), itemReq.productId(), sku, name, unitPrice, itemReq.qty());
            items.add(orderItem);

            eventItems.add(Map.of(
                    "productId", itemReq.productId().toString(),
                    "sku", sku,
                    "name", name,
                    "unitPrice", unitPrice,
                    "qty", itemReq.qty()
            ));
        }

        Order order = new Order(orderId, req.customerId(), totalAmount, req.currency());
        for (OrderItem oi : items) {
            order.addItem(oi);
        }

        Order saved = orderRepository.save(order);

        // Record outbox event in same transaction
        Map<String, Object> outboxPayload = Map.of(
                "orderId", orderId.toString(),
                "customerId", req.customerId().toString(),
                "totalAmount", totalAmount,
                "currency", order.getCurrency(),
                "items", eventItems
        );

        try {
            String payloadJson = objectMapper.writeValueAsString(outboxPayload);
            OutboxEvent outboxEvent = new OutboxEvent(
                    UUID.randomUUID(),
                    "Order",
                    orderId.toString(),
                    "order.created",
                    payloadJson
            );
            outboxEventRepository.save(outboxEvent);
            log.info("Saved order {} and outbox_event in same transaction", orderId);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize outbox event payload", e);
        }

        return toDto(saved);
    }

    @Transactional
    public OrderDto cancelOrder(UUID id, String reason) {
        Order order = orderRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + id));

        if (order.getStatus() == OrderStatus.DELIVERED || order.getStatus() == OrderStatus.CANCELLED) {
            throw new InvalidOrderStateException("Order in status " + order.getStatus() + " cannot be cancelled");
        }

        order.cancel(reason);
        Order updated = orderRepository.save(order);

        // Record cancellation outbox event
        try {
            String payload = objectMapper.writeValueAsString(Map.of(
                    "orderId", id.toString(),
                    "status", "CANCELLED",
                    "reason", reason,
                    "timestamp", java.time.Instant.now().toString()
            ));
            outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", id.toString(), "order.cancelled", payload));
        } catch (Exception e) {
            log.warn("Failed to create cancellation outbox event: {}", e.getMessage());
        }

        return toDto(updated);
    }

    @Transactional
    public void confirmOrder(UUID orderId) {
        orderRepository.findById(orderId).ifPresent(order -> {
            if (order.getStatus() == OrderStatus.PENDING) {
                order.transitionTo(OrderStatus.CONFIRMED);
                orderRepository.save(order);
                log.info("Choreography: Order {} transitioned to CONFIRMED", orderId);

                try {
                    String payload = objectMapper.writeValueAsString(Map.of(
                            "orderId", orderId.toString(),
                            "status", "CONFIRMED",
                            "timestamp", java.time.Instant.now().toString()
                    ));
                    outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", orderId.toString(), "order.confirmed", payload));
                } catch (Exception e) {
                    log.warn("Failed to create confirmation outbox event: {}", e.getMessage());
                }
            }
        });
    }

    @Transactional
    public void rejectOrder(UUID orderId, String reason) {
        orderRepository.findById(orderId).ifPresent(order -> {
            if (order.getStatus() == OrderStatus.PENDING) {
                order.cancel("INSUFFICIENT_STOCK: " + reason);
                orderRepository.save(order);
                log.info("Choreography: Order {} transitioned to CANCELLED (insufficient stock)", orderId);

                try {
                    String payload = objectMapper.writeValueAsString(Map.of(
                            "orderId", orderId.toString(),
                            "status", "CANCELLED",
                            "reason", "INSUFFICIENT_STOCK: " + reason,
                            "timestamp", java.time.Instant.now().toString()
                    ));
                    outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", orderId.toString(), "order.cancelled", payload));
                } catch (Exception e) {
                    log.warn("Failed to create rejection outbox event: {}", e.getMessage());
                }
            }
        });
    }

    public OrderDto toDto(Order order) {
        List<OrderItemDto> itemDtos = order.getItems().stream().map(i -> new OrderItemDto(
                i.getId(),
                i.getProductId(),
                i.getSku(),
                i.getProductName(),
                i.getUnitPrice(),
                i.getQty(),
                i.getUnitPrice().multiply(BigDecimal.valueOf(i.getQty()))
        )).toList();

        return new OrderDto(
                order.getId(),
                order.getCustomerId(),
                order.getStatus(),
                order.getTotalAmount(),
                order.getCurrency(),
                order.getCancelReason(),
                itemDtos,
                order.getCreatedAt(),
                order.getUpdatedAt(),
                order.getVersion()
        );
    }
}
