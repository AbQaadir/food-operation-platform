package com.foodplatform.identity.dto;

import com.foodplatform.identity.domain.Role;

import java.time.Instant;
import java.util.UUID;

public record UserDto(
        UUID id,
        String email,
        String fullName,
        Role role,
        boolean enabled,
        Instant createdAt
) {}
