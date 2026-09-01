package com.foodplatform.identity.dto;

public record AuthResponse(
        String accessToken,
        String refreshToken,
        long expiresIn,
        UserDto user
) {}
