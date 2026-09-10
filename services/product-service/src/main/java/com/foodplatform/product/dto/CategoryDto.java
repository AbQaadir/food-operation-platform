package com.foodplatform.product.dto;

import java.time.Instant;
import java.util.UUID;

public record CategoryDto(
        UUID id,
        String name,
        UUID parentId,
        Instant createdAt
) {}
