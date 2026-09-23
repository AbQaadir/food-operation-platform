package com.foodplatform.inventory.dto;

import java.time.Instant;
import java.util.UUID;

public record WarehouseDto(
        UUID id,
        String code,
        String name,
        String location,
        Instant createdAt
) {}
