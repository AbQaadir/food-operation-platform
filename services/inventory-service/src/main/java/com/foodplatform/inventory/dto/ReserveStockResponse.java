package com.foodplatform.inventory.dto;

import java.util.List;
import java.util.UUID;

public record ReserveStockResponse(
        UUID orderId,
        boolean success,
        List<ReservationItemResultDto> reservations,
        String message
) {}
