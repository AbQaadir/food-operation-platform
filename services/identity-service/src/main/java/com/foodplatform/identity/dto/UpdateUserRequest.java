package com.foodplatform.identity.dto;

import com.foodplatform.identity.domain.Role;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record UpdateUserRequest(
        @NotBlank(message = "Full name is required")
        String fullName,

        @NotNull(message = "Role is required")
        Role role,

        Boolean enabled
) {}
