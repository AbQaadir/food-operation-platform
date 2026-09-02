package com.foodplatform.identity.service;

import com.foodplatform.identity.domain.RefreshToken;
import com.foodplatform.identity.domain.Role;
import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.dto.AuthResponse;
import com.foodplatform.identity.dto.LoginRequest;
import com.foodplatform.identity.dto.RegisterRequest;
import com.foodplatform.identity.dto.UserDto;
import com.foodplatform.identity.exception.InvalidCredentialsException;
import com.foodplatform.identity.exception.UserAlreadyExistsException;
import com.foodplatform.identity.repository.RefreshTokenRepository;
import com.foodplatform.identity.repository.UserRepository;
import com.foodplatform.identity.security.JwtTokenProvider;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthService(
            UserRepository userRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider jwtTokenProvider
    ) {
        this.userRepository = userRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmailIgnoreCase(request.email())) {
            throw new UserAlreadyExistsException("Email already registered: " + request.email());
        }

        User user = new User(
                UUID.randomUUID(),
                request.email().toLowerCase().trim(),
                passwordEncoder.encode(request.password()),
                request.fullName().trim(),
                Role.CUSTOMER,
                true
        );

        User saved = userRepository.save(user);
        return createAuthResponse(saved);
    }

    @Transactional
    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmailIgnoreCase(request.email().trim())
                .orElseThrow(() -> new InvalidCredentialsException("Invalid email or password"));

        if (!user.isEnabled()) {
            throw new InvalidCredentialsException("Account is disabled");
        }

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new InvalidCredentialsException("Invalid email or password");
        }

        return createAuthResponse(user);
    }

    @Transactional
    public AuthResponse refresh(String refreshTokenString) {
        RefreshToken token = refreshTokenRepository.findByTokenHash(refreshTokenString)
                .orElseThrow(() -> new InvalidCredentialsException("Invalid refresh token"));

        if (token.isRevoked() || token.getExpiresAt().isBefore(Instant.now())) {
            throw new InvalidCredentialsException("Refresh token is expired or revoked");
        }

        User user = userRepository.findById(token.getUserId())
                .orElseThrow(() -> new InvalidCredentialsException("User not found"));

        token.setRevoked(true);
        refreshTokenRepository.save(token);

        return createAuthResponse(user);
    }

    private AuthResponse createAuthResponse(User user) {
        String accessToken = jwtTokenProvider.generateAccessToken(user);
        String refreshTokenStr = jwtTokenProvider.generateRefreshTokenString();

        RefreshToken refreshToken = new RefreshToken(
                UUID.randomUUID(),
                user.getId(),
                refreshTokenStr,
                Instant.now().plusSeconds(jwtTokenProvider.getRefreshExpirationSeconds())
        );
        refreshTokenRepository.save(refreshToken);

        UserDto userDto = new UserDto(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getRole(),
                user.isEnabled(),
                user.getCreatedAt()
        );

        return new AuthResponse(
                accessToken,
                refreshTokenStr,
                jwtTokenProvider.getAccessExpirationSeconds(),
                userDto
        );
    }
}
