package com.foodplatform.order.client;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@Component
public class ProductClient {

    private static final Logger log = LoggerFactory.getLogger(ProductClient.class);

    private final RestClient restClient;

    public ProductClient(@Value("${clients.product-service.url:http://localhost:8082}") String productServiceUrl) {
        this.restClient = RestClient.builder().baseUrl(productServiceUrl).build();
    }

    public record ProductInfo(UUID id, String sku, String name, BigDecimal price, boolean active) {}

    @CircuitBreaker(name = "productClient", fallbackMethod = "fetchProductFallback")
    @Retry(name = "productClient")
    public ProductInfo fetchProduct(UUID productId) {
        log.info("Calling product-service for product {}", productId);
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restClient.get()
                    .uri("/api/v1/products/{id}", productId)
                    .retrieve()
                    .body(Map.class);

            if (resp != null) {
                return new ProductInfo(
                        UUID.fromString(resp.get("id").toString()),
                        resp.get("sku").toString(),
                        resp.get("name").toString(),
                        new BigDecimal(resp.get("price").toString()),
                        Boolean.parseBoolean(resp.get("active").toString())
                );
            }
        } catch (Exception e) {
            log.warn("Product client error for {}: {}", productId, e.getMessage());
        }
        return fetchProductFallback(productId, new RuntimeException("Product service unavailable"));
    }

    public ProductInfo fetchProductFallback(UUID productId, Throwable t) {
        log.warn("Executing fallback for product {} due to: {}", productId, t.getMessage());
        return new ProductInfo(productId, "SKU-UNKNOWN", "Product " + productId, new BigDecimal("10.00"), true);
    }
}
