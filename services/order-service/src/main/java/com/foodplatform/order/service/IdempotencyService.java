package com.foodplatform.order.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.domain.IdempotencyRecord;
import com.foodplatform.order.repository.IdempotencyRecordRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Optional;

@Service
public class IdempotencyService {

    private static final Logger log = LoggerFactory.getLogger(IdempotencyService.class);
    private static final String REDIS_PREFIX = "idempotency:";
    private static final Duration TTL = Duration.ofHours(24);

    private final IdempotencyRecordRepository repository;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    public IdempotencyService(IdempotencyRecordRepository repository,
                              @Autowired(required = false) StringRedisTemplate redisTemplate,
                              ObjectMapper objectMapper) {
        this.repository = repository;
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    public record CachedResponse(int statusCode, String body) {}

    public Optional<CachedResponse> getCachedResponse(String key) {
        if (key == null || key.isBlank()) return Optional.empty();

        // 1. Try Redis cache
        if (redisTemplate != null) {
            try {
                String cached = redisTemplate.opsForValue().get(REDIS_PREFIX + key);
                if (cached != null) {
                    CachedResponse cr = objectMapper.readValue(cached, CachedResponse.class);
                    log.info("Idempotency HIT from Redis for key: {}", key);
                    return Optional.of(cr);
                }
            } catch (Exception e) {
                log.warn("Redis idempotency read failed for {}: {}", key, e.getMessage());
            }
        }

        // 2. Fall back to PostgreSQL database
        Optional<IdempotencyRecord> record = repository.findById(key);
        if (record.isPresent()) {
            log.info("Idempotency HIT from DB for key: {}", key);
            CachedResponse cr = new CachedResponse(record.get().getStatusCode(), record.get().getResponseBody());
            // Warm Redis
            saveToRedis(key, cr);
            return Optional.of(cr);
        }

        return Optional.empty();
    }

    public void saveResponse(String key, int statusCode, String responseBody) {
        if (key == null || key.isBlank()) return;

        CachedResponse cr = new CachedResponse(statusCode, responseBody);

        // 1. Save to DB
        try {
            repository.save(new IdempotencyRecord(key, responseBody, statusCode));
        } catch (Exception e) {
            log.warn("DB idempotency save failed for {}: {}", key, e.getMessage());
        }

        // 2. Save to Redis
        saveToRedis(key, cr);
    }

    private void saveToRedis(String key, CachedResponse cr) {
        if (redisTemplate != null) {
            try {
                String json = objectMapper.writeValueAsString(cr);
                redisTemplate.opsForValue().set(REDIS_PREFIX + key, json, TTL);
            } catch (Exception e) {
                log.warn("Redis idempotency write failed for {}: {}", key, e.getMessage());
            }
        }
    }
}
