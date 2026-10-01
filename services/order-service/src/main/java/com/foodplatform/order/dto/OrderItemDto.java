package com.foodplatform.order.dto;

import java.math.BigDecimal;
import java.util.UUID;

public record OrderItemDto(
        UUID id,
        UUID productId,
        String sku,
        String productName,
        BigDecimal unitPrice,
        int qty,
        BigDecimal subtotal
) {}
