package com.foodplatform.order.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public record CreateOrderItemRequest(
        @NotNull UUID productId,
        String sku,
        String productName,
        BigDecimal unitPrice,
        @Min(1) int qty
) {}
