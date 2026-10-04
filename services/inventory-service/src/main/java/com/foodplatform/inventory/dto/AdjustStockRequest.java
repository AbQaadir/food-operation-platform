package com.foodplatform.inventory.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record AdjustStockRequest(
        @NotNull UUID warehouseId,
        @NotNull UUID productId,
        int delta,
        String reason,
        String refId
) {}
