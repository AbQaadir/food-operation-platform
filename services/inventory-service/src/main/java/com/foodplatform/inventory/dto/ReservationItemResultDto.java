package com.foodplatform.inventory.dto;

import java.util.UUID;

public record ReservationItemResultDto(
        UUID productId,
        UUID warehouseId,
        int qty,
        boolean success
) {}
