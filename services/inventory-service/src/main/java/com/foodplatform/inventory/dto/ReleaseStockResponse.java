package com.foodplatform.inventory.dto;

import java.util.UUID;

public record ReleaseStockResponse(
        UUID orderId,
        int releasedCount,
        String message
) {}
