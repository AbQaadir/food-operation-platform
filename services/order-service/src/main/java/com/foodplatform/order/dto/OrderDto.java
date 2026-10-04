package com.foodplatform.order.dto;

import com.foodplatform.order.domain.OrderStatus;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record OrderDto(
        UUID id,
        UUID customerId,
        OrderStatus status,
        BigDecimal totalAmount,
        String currency,
        String cancelReason,
        List<OrderItemDto> items,
        Instant createdAt,
        Instant updatedAt,
        Long version
) {}
