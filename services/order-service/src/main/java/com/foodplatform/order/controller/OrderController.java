package com.foodplatform.order.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.domain.OrderStatus;
import com.foodplatform.order.dto.*;
import com.foodplatform.order.service.IdempotencyService;
import com.foodplatform.order.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/orders")
@Tag(name = "Orders", description = "Order lifecycle, idempotency, and transactional outbox management")
public class OrderController {

    private final OrderService orderService;
    private final IdempotencyService idempotencyService;
    private final ObjectMapper objectMapper;

    public OrderController(OrderService orderService,
                           IdempotencyService idempotencyService,
                           ObjectMapper objectMapper) {
        this.orderService = orderService;
        this.idempotencyService = idempotencyService;
        this.objectMapper = objectMapper;
    }

    @PostMapping
    @Operation(summary = "Create new order with idempotency key")
    public ResponseEntity<?> createOrder(
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey,
            @Valid @RequestBody CreateOrderRequest request
    ) throws Exception {
        // Idempotency-Key is mandatory per platform API contract (spec §5.4)
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            throw new MissingIdempotencyKeyException();
        }
        Optional<IdempotencyService.CachedResponse> cached = idempotencyService.getCachedResponse(idempotencyKey);
        if (cached.isPresent()) {
            OrderDto cachedDto = objectMapper.readValue(cached.get().body(), OrderDto.class);
            return ResponseEntity.status(cached.get().statusCode()).body(cachedDto);
        }

        OrderDto created = orderService.createOrder(request);

        String json = objectMapper.writeValueAsString(created);
        idempotencyService.saveResponse(idempotencyKey, HttpStatus.CREATED.value(), json);

        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID")
    public ResponseEntity<OrderDto> getOrderById(@PathVariable UUID id) {
        return ResponseEntity.ok(orderService.getOrderById(id));
    }

    @GetMapping
    @Operation(summary = "List orders with filters and pagination")
    public ResponseEntity<PagedResponse<OrderDto>> getOrders(
            @RequestParam(required = false) UUID customerId,
            @RequestParam(required = false) OrderStatus status,
            @PageableDefault(size = 20) Pageable pageable
    ) {
        return ResponseEntity.ok(orderService.getOrders(customerId, status, pageable));
    }

    @PostMapping("/{id}/cancel")
    @Operation(summary = "Cancel an order")
    public ResponseEntity<OrderDto> cancelOrder(
            @PathVariable UUID id,
            @Valid @RequestBody CancelOrderRequest request
    ) {
        return ResponseEntity.ok(orderService.cancelOrder(id, request.reason()));
    }
}
