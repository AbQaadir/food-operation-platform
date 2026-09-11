package com.foodplatform.product.controller;

import com.foodplatform.product.dto.CreateProductRequest;
import com.foodplatform.product.dto.PagedResponse;
import com.foodplatform.product.dto.ProductDto;
import com.foodplatform.product.dto.UpdateProductRequest;
import com.foodplatform.product.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/products")
@Tag(name = "Products", description = "Product Catalog Operations")
public class ProductController {

    private final ProductService productService;

    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    @GetMapping
    @Operation(summary = "List and filter products with pagination")
    public ResponseEntity<PagedResponse<ProductDto>> getProducts(
            @RequestParam(required = false) UUID category,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            @RequestParam(required = false) Boolean active,
            @PageableDefault(page = 0, size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable
    ) {
        PagedResponse<ProductDto> response = productService.getProducts(category, q, minPrice, maxPrice, active, pageable);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get product by ID (cached)")
    public ResponseEntity<ProductDto> getProductById(@PathVariable UUID id) {
        ProductDto product = productService.getProductById(id);
        return ResponseEntity.ok(product);
    }

    @PostMapping
    @Operation(summary = "Create a new product")
    public ResponseEntity<ProductDto> createProduct(@Valid @RequestBody CreateProductRequest request) {
        ProductDto created = productService.createProduct(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update an existing product")
    public ResponseEntity<ProductDto> updateProduct(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateProductRequest request
    ) {
        ProductDto updated = productService.updateProduct(id, request);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a product")
    public ResponseEntity<Void> deleteProduct(@PathVariable UUID id) {
        productService.deleteProduct(id);
        return ResponseEntity.noContent().build();
    }
}
