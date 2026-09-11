package com.foodplatform.product.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public record UpdateProductRequest(
        @NotBlank(message = "Product name is required")
        String name,

        String description,

        UUID categoryId,

        @NotBlank(message = "Unit is required")
        String unit,

        @NotNull(message = "Price is required")
        @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
        BigDecimal price,

        String currency,

        Boolean active
) {}
