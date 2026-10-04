package com.foodplatform.product.service;

import com.foodplatform.product.domain.Product;
import com.foodplatform.product.dto.CreateProductRequest;
import com.foodplatform.product.dto.PagedResponse;
import com.foodplatform.product.dto.ProductDto;
import com.foodplatform.product.dto.UpdateProductRequest;
import com.foodplatform.product.exception.DuplicateResourceException;
import com.foodplatform.product.exception.ResourceNotFoundException;
import com.foodplatform.product.repository.ProductRepository;
import com.foodplatform.product.repository.ProductSpecifications;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;

@Service
public class ProductService {

    private static final Logger log = LoggerFactory.getLogger(ProductService.class);

    private final ProductRepository productRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public ProductService(ProductRepository productRepository,
                          @Autowired(required = false) KafkaTemplate<String, Object> kafkaTemplate) {
        this.productRepository = productRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Transactional(readOnly = true)
    public PagedResponse<ProductDto> getProducts(
            UUID categoryId,
            String query,
            BigDecimal minPrice,
            BigDecimal maxPrice,
            Boolean active,
            Pageable pageable
    ) {
        Specification<Product> spec = ProductSpecifications.withFilters(categoryId, query, minPrice, maxPrice, active);
        Page<Product> page = productRepository.findAll(spec, pageable);
        return PagedResponse.from(page.map(this::toDto));
    }

    @Cacheable(value = "products", key = "#id")
    @Transactional(readOnly = true)
    public ProductDto getProductById(UUID id) {
        log.info("Fetching product from database for id: {}", id);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        return toDto(product);
    }

    @Transactional
    public ProductDto createProduct(CreateProductRequest request) {
        if (productRepository.existsBySku(request.sku())) {
            throw new DuplicateResourceException("Product with SKU already exists: " + request.sku());
        }

        Product product = new Product(
                UUID.randomUUID(),
                request.sku().trim().toUpperCase(),
                request.name().trim(),
                request.description(),
                request.categoryId(),
                request.unit(),
                request.price(),
                request.currency() != null ? request.currency() : "USD",
                request.active() != null ? request.active() : true
        );

        Product saved = productRepository.save(product);
        publishProductEvent("product.created", saved);
        return toDto(saved);
    }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public ProductDto updateProduct(UUID id, UpdateProductRequest request) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));

        product.setName(request.name().trim());
        product.setDescription(request.description());
        product.setCategoryId(request.categoryId());
        product.setUnit(request.unit());
        product.setPrice(request.price());
        if (request.currency() != null) {
            product.setCurrency(request.currency());
        }
        if (request.active() != null) {
            product.setActive(request.active());
        }

        Product updated = productRepository.save(product);
        publishProductEvent("product.updated", updated);
        return toDto(updated);
    }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public void deleteProduct(UUID id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        productRepository.delete(product);
        publishProductEvent("product.deleted", product);
    }

    private void publishProductEvent(String topic, Product product) {
        if (kafkaTemplate != null) {
            try {
                Map<String, Object> payload = Map.of(
                        "productId", product.getId().toString(),
                        "sku", product.getSku(),
                        "name", product.getName(),
                        "price", product.getPrice(),
                        "active", product.isActive()
                );
                kafkaTemplate.send("product.updated", product.getId().toString(), payload);
            } catch (Exception e) {
                log.warn("Failed to publish event for product {}: {}", product.getId(), e.getMessage());
            }
        }
    }

    public ProductDto toDto(Product product) {
        return new ProductDto(
                product.getId(),
                product.getSku(),
                product.getName(),
                product.getDescription(),
                product.getCategoryId(),
                product.getUnit(),
                product.getPrice(),
                product.getCurrency(),
                product.isActive(),
                product.getCreatedAt(),
                product.getUpdatedAt(),
                product.getVersion()
        );
    }
}
