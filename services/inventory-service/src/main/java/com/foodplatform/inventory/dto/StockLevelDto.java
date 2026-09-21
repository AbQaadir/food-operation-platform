package com.foodplatform.inventory.dto;

import java.time.Instant;
import java.util.UUID;

public record StockLevelDto(
        UUID id,
        UUID warehouseId,
        String warehouseCode,
        String warehouseName,
        UUID productId,
        int onHand,
        int reserved,
        int available,
        int lowStockThreshold,
        Long version,
        Instant updatedAt
) {}
