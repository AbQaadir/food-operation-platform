package com.foodplatform.product.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.UUID;

public record CreateCategoryRequest(
        @NotBlank(message = "Category name must not be blank")
        String name,
        UUID parentId
) {}
