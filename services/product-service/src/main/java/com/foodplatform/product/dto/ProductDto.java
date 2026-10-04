package com.foodplatform.product.dto;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

public record ProductDto(
        UUID id,
        String sku,
        String name,
        String description,
        UUID categoryId,
        String unit,
        BigDecimal price,
        String currency,
        boolean active,
        Instant createdAt,
        Instant updatedAt,
        Long version
) implements Serializable {}
