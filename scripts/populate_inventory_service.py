#!/usr/bin/env python3
import os

BASE = "/Users/qaadir/Desktop/dev/foodOperationPlatform/services/inventory-service/src/main/java/com/foodplatform/inventory"

FILES = {
    # Main Application
    f"{BASE}/InventoryServiceApplication.java": """package com.foodplatform.inventory;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class InventoryServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(InventoryServiceApplication.class, args);
    }
}
""",

    # Domain: Warehouse
    f"{BASE}/domain/Warehouse.java": """package com.foodplatform.inventory.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "warehouses")
public class Warehouse {

    @Id
    private UUID id;

    @Column(nullable = false, unique = true, length = 50)
    private String code;

    @Column(nullable = false)
    private String name;

    private String location;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public Warehouse() {}

    public Warehouse(UUID id, String code, String name, String location) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.location = location;
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
""",

    # Domain: StockLevel
    f"{BASE}/domain/StockLevel.java": """package com.foodplatform.inventory.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "stock_levels", uniqueConstraints = {
        @UniqueConstraint(columnNames = {"warehouse_id", "product_id"})
})
public class StockLevel {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "warehouse_id", nullable = false)
    private Warehouse warehouse;

    @Column(name = "product_id", nullable = false)
    private UUID productId;

    @Column(name = "on_hand", nullable = false)
    private int onHand;

    @Column(name = "reserved", nullable = false)
    private int reserved;

    @Column(name = "low_stock_threshold", nullable = false)
    private int lowStockThreshold;

    @Version
    @Column(nullable = false)
    private Long version;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    public StockLevel() {}

    public StockLevel(UUID id, Warehouse warehouse, UUID productId, int onHand, int reserved, int lowStockThreshold) {
        this.id = id;
        this.warehouse = warehouse;
        this.productId = productId;
        this.onHand = onHand;
        this.reserved = reserved;
        this.lowStockThreshold = lowStockThreshold;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public int getAvailable() {
        return onHand - reserved;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public Warehouse getWarehouse() { return warehouse; }
    public void setWarehouse(Warehouse warehouse) { this.warehouse = warehouse; }

    public UUID getProductId() { return productId; }
    public void setProductId(UUID productId) { this.productId = productId; }

    public int getOnHand() { return onHand; }
    public void setOnHand(int onHand) { this.onHand = onHand; }

    public int getReserved() { return reserved; }
    public void setReserved(int reserved) { this.reserved = reserved; }

    public int getLowStockThreshold() { return lowStockThreshold; }
    public void setLowStockThreshold(int lowStockThreshold) { this.lowStockThreshold = lowStockThreshold; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
""",

    # Domain: ReservationStatus
    f"{BASE}/domain/ReservationStatus.java": """package com.foodplatform.inventory.domain;

public enum ReservationStatus {
    ACTIVE,
    RELEASED,
    CONSUMED
}
""",

    # Domain: Reservation
    f"{BASE}/domain/Reservation.java": """package com.foodplatform.inventory.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "reservations")
public class Reservation {

    @Id
    private UUID id;

    @Column(name = "order_id", nullable = false)
    private UUID orderId;

    @Column(name = "product_id", nullable = false)
    private UUID productId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "warehouse_id", nullable = false)
    private Warehouse warehouse;

    @Column(nullable = false)
    private int qty;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private ReservationStatus status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    public Reservation() {}

    public Reservation(UUID id, UUID orderId, UUID productId, Warehouse warehouse, int qty, ReservationStatus status) {
        this.id = id;
        this.orderId = orderId;
        this.productId = productId;
        this.warehouse = warehouse;
        this.qty = qty;
        this.status = status;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getOrderId() { return orderId; }
    public void setOrderId(UUID orderId) { this.orderId = orderId; }

    public UUID getProductId() { return productId; }
    public void setProductId(UUID productId) { this.productId = productId; }

    public Warehouse getWarehouse() { return warehouse; }
    public void setWarehouse(Warehouse warehouse) { this.warehouse = warehouse; }

    public int getQty() { return qty; }
    public void setQty(int qty) { this.qty = qty; }

    public ReservationStatus getStatus() { return status; }
    public void setStatus(ReservationStatus status) { this.status = status; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
""",

    # Domain: StockMovement
    f"{BASE}/domain/StockMovement.java": """package com.foodplatform.inventory.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "stock_movements")
public class StockMovement {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "stock_level_id", nullable = false)
    private StockLevel stockLevel;

    @Column(nullable = false)
    private int delta;

    @Column(nullable = false)
    private String reason;

    @Column(name = "ref_id")
    private String refId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public StockMovement() {}

    public StockMovement(UUID id, StockLevel stockLevel, int delta, String reason, String refId) {
        this.id = id;
        this.stockLevel = stockLevel;
        this.delta = delta;
        this.reason = reason;
        this.refId = refId;
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public StockLevel getStockLevel() { return stockLevel; }
    public void setStockLevel(StockLevel stockLevel) { this.stockLevel = stockLevel; }

    public int getDelta() { return delta; }
    public void setDelta(int delta) { this.delta = delta; }

    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }

    public String getRefId() { return refId; }
    public void setRefId(String refId) { this.refId = refId; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
""",

    # Exceptions
    f"{BASE}/exception/ResourceNotFoundException.java": """package com.foodplatform.inventory.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
""",

    f"{BASE}/exception/DuplicateResourceException.java": """package com.foodplatform.inventory.exception;

public class DuplicateResourceException extends RuntimeException {
    public DuplicateResourceException(String message) {
        super(message);
    }
}
""",

    f"{BASE}/exception/InsufficientStockException.java": """package com.foodplatform.inventory.exception;

public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(String message) {
        super(message);
    }
}
""",

    f"{BASE}/exception/GlobalExceptionHandler.java": """package com.foodplatform.inventory.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.time.Instant;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.NOT_FOUND, "Resource Not Found", ex.getMessage(), "not-found", request);
    }

    @ExceptionHandler(DuplicateResourceException.class)
    public ProblemDetail handleDuplicate(DuplicateResourceException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.CONFLICT, "Duplicate Resource", ex.getMessage(), "duplicate-resource", request);
    }

    @ExceptionHandler(InsufficientStockException.class)
    public ProblemDetail handleInsufficientStock(InsufficientStockException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.CONFLICT, "Insufficient Stock", ex.getMessage(), "insufficient-stock", request);
    }

    @ExceptionHandler(OptimisticLockingFailureException.class)
    public ProblemDetail handleOptimisticLocking(OptimisticLockingFailureException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.CONFLICT, "Concurrency Conflict", "Resource was concurrently modified, please retry", "concurrency-conflict", request);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex, WebRequest request) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Validation Error", detail, "validation-error", request);
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneric(Exception ex, WebRequest request) {
        log.error("Unhandled exception in inventory-service", ex);
        return buildProblemDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", ex.getMessage(), "internal", request);
    }

    private ProblemDetail buildProblemDetail(HttpStatus status, String title, String detail, String typeCode, WebRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(title);
        pd.setType(URI.create("https://foodplatform.com/errors/" + typeCode));
        pd.setProperty("timestamp", Instant.now());
        if (request instanceof ServletWebRequest swr) {
            pd.setInstance(URI.create(swr.getRequest().getRequestURI()));
            String correlationId = swr.getHeader("X-Correlation-Id");
            if (correlationId != null) {
                pd.setProperty("correlationId", correlationId);
            }
        }
        return pd;
    }
}
""",

    # Repositories
    f"{BASE}/repository/WarehouseRepository.java": """package com.foodplatform.inventory.repository;

import com.foodplatform.inventory.domain.Warehouse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface WarehouseRepository extends JpaRepository<Warehouse, UUID> {
    Optional<Warehouse> findByCode(String code);
    boolean existsByCode(String code);
}
""",

    f"{BASE}/repository/StockLevelRepository.java": """package com.foodplatform.inventory.repository;

import com.foodplatform.inventory.domain.StockLevel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface StockLevelRepository extends JpaRepository<StockLevel, UUID> {

    List<StockLevel> findByProductId(UUID productId);

    Optional<StockLevel> findByWarehouseIdAndProductId(UUID warehouseId, UUID productId);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("UPDATE StockLevel s SET s.reserved = s.reserved + :qty, s.version = s.version + 1, s.updatedAt = CURRENT_TIMESTAMP " +
           "WHERE s.id = :id AND (s.onHand - s.reserved) >= :qty")
    int reserveStockConditional(@Param("id") UUID id, @Param("qty") int qty);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("UPDATE StockLevel s SET s.reserved = s.reserved - :qty, s.version = s.version + 1, s.updatedAt = CURRENT_TIMESTAMP " +
           "WHERE s.id = :id AND s.reserved >= :qty")
    int releaseStockConditional(@Param("id") UUID id, @Param("qty") int qty);
}
""",

    f"{BASE}/repository/ReservationRepository.java": """package com.foodplatform.inventory.repository;

import com.foodplatform.inventory.domain.Reservation;
import com.foodplatform.inventory.domain.ReservationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReservationRepository extends JpaRepository<Reservation, UUID> {
    List<Reservation> findByOrderId(UUID orderId);
    List<Reservation> findByOrderIdAndStatus(UUID orderId, ReservationStatus status);
}
""",

    f"{BASE}/repository/StockMovementRepository.java": """package com.foodplatform.inventory.repository;

import com.foodplatform.inventory.domain.StockMovement;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface StockMovementRepository extends JpaRepository<StockMovement, UUID> {
}
""",

    # DTOs
    f"{BASE}/dto/WarehouseDto.java": """package com.foodplatform.inventory.dto;

import java.time.Instant;
import java.util.UUID;

public record WarehouseDto(
        UUID id,
        String code,
        String name,
        String location,
        Instant createdAt
) {}
""",

    f"{BASE}/dto/CreateWarehouseRequest.java": """package com.foodplatform.inventory.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateWarehouseRequest(
        @NotBlank @Size(max = 50) String code,
        @NotBlank @Size(max = 255) String name,
        String location
) {}
""",

    f"{BASE}/dto/StockLevelDto.java": """package com.foodplatform.inventory.dto;

import java.time.Instant;
import java.util.UUID;

public record StockLevelDto(
        UUID id,
        UUID warehouseId,
        String warehouseCode,
        String warehouseName,
        UUID productId,
        int onHand,
        int reserved,
        int available,
        int lowStockThreshold,
        Long version,
        Instant updatedAt
) {}
""",

    f"{BASE}/dto/AdjustStockRequest.java": """package com.foodplatform.inventory.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record AdjustStockRequest(
        @NotNull UUID warehouseId,
        @NotNull UUID productId,
        int delta,
        String reason,
        String refId
) {}
""",

    f"{BASE}/dto/OrderItemRequest.java": """package com.foodplatform.inventory.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record OrderItemRequest(
        @NotNull UUID productId,
        @Min(1) int qty
) {}
""",

    f"{BASE}/dto/ReserveStockRequest.java": """package com.foodplatform.inventory.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

public record ReserveStockRequest(
        @NotNull UUID orderId,
        @NotEmpty @Valid List<OrderItemRequest> items
) {}
""",

    f"{BASE}/dto/ReservationItemResultDto.java": """package com.foodplatform.inventory.dto;

import java.util.UUID;

public record ReservationItemResultDto(
        UUID productId,
        UUID warehouseId,
        int qty,
        boolean success
) {}
""",

    f"{BASE}/dto/ReserveStockResponse.java": """package com.foodplatform.inventory.dto;

import java.util.List;
import java.util.UUID;

public record ReserveStockResponse(
        UUID orderId,
        boolean success,
        List<ReservationItemResultDto> reservations,
        String message
) {}
""",

    f"{BASE}/dto/ReleaseStockRequest.java": """package com.foodplatform.inventory.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record ReleaseStockRequest(
        @NotNull UUID orderId
) {}
""",

    f"{BASE}/dto/ReleaseStockResponse.java": """package com.foodplatform.inventory.dto;

import java.util.UUID;

public record ReleaseStockResponse(
        UUID orderId,
        int releasedCount,
        String message
) {}
""",

    # Services: WarehouseService & InventoryService
    f"{BASE}/service/WarehouseService.java": """package com.foodplatform.inventory.service;

import com.foodplatform.inventory.domain.Warehouse;
import com.foodplatform.inventory.dto.CreateWarehouseRequest;
import com.foodplatform.inventory.dto.WarehouseDto;
import com.foodplatform.inventory.exception.DuplicateResourceException;
import com.foodplatform.inventory.exception.ResourceNotFoundException;
import com.foodplatform.inventory.repository.WarehouseRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class WarehouseService {

    private final WarehouseRepository warehouseRepository;

    public WarehouseService(WarehouseRepository warehouseRepository) {
        this.warehouseRepository = warehouseRepository;
    }

    @Transactional(readOnly = true)
    public List<WarehouseDto> getAllWarehouses() {
        return warehouseRepository.findAll().stream().map(this::toDto).toList();
    }

    @Transactional(readOnly = true)
    public WarehouseDto getWarehouseById(UUID id) {
        return warehouseRepository.findById(id)
                .map(this::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Warehouse not found: " + id));
    }

    @Transactional
    public WarehouseDto createWarehouse(CreateWarehouseRequest req) {
        if (warehouseRepository.existsByCode(req.code().trim().toUpperCase())) {
            throw new DuplicateResourceException("Warehouse with code already exists: " + req.code());
        }
        Warehouse w = new Warehouse(
                UUID.randomUUID(),
                req.code().trim().toUpperCase(),
                req.name().trim(),
                req.location()
        );
        return toDto(warehouseRepository.save(w));
    }

    public WarehouseDto toDto(Warehouse w) {
        return new WarehouseDto(w.getId(), w.getCode(), w.getName(), w.getLocation(), w.getCreatedAt());
    }
}
""",

    f"{BASE}/service/InventoryService.java": """package com.foodplatform.inventory.service;

import com.foodplatform.inventory.domain.*;
import com.foodplatform.inventory.dto.*;
import com.foodplatform.inventory.exception.InsufficientStockException;
import com.foodplatform.inventory.exception.ResourceNotFoundException;
import com.foodplatform.inventory.repository.ReservationRepository;
import com.foodplatform.inventory.repository.StockLevelRepository;
import com.foodplatform.inventory.repository.StockMovementRepository;
import com.foodplatform.inventory.repository.WarehouseRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class InventoryService {

    private static final Logger log = LoggerFactory.getLogger(InventoryService.class);

    private final StockLevelRepository stockLevelRepository;
    private final ReservationRepository reservationRepository;
    private final StockMovementRepository stockMovementRepository;
    private final WarehouseRepository warehouseRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public InventoryService(StockLevelRepository stockLevelRepository,
                            ReservationRepository reservationRepository,
                            StockMovementRepository stockMovementRepository,
                            WarehouseRepository warehouseRepository,
                            @Autowired(required = false) KafkaTemplate<String, Object> kafkaTemplate) {
        this.stockLevelRepository = stockLevelRepository;
        this.reservationRepository = reservationRepository;
        this.stockMovementRepository = stockMovementRepository;
        this.warehouseRepository = warehouseRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Transactional(readOnly = true)
    public List<StockLevelDto> getProductStock(UUID productId) {
        return stockLevelRepository.findByProductId(productId).stream()
                .map(this::toDto)
                .toList();
    }

    @Transactional
    public StockLevelDto adjustStock(AdjustStockRequest req) {
        Warehouse warehouse = warehouseRepository.findById(req.warehouseId())
                .orElseThrow(() -> new ResourceNotFoundException("Warehouse not found: " + req.warehouseId()));

        StockLevel stock = stockLevelRepository.findByWarehouseIdAndProductId(req.warehouseId(), req.productId())
                .orElseGet(() -> new StockLevel(UUID.randomUUID(), warehouse, req.productId(), 0, 0, 10));

        int newOnHand = stock.getOnHand() + req.delta();
        if (newOnHand < stock.getReserved()) {
            throw new InsufficientStockException("Cannot adjust stock below current reservations. Current reserved: " + stock.getReserved() + ", requested on-hand: " + newOnHand);
        }
        if (newOnHand < 0) {
            throw new InsufficientStockException("On-hand stock cannot be negative");
        }

        stock.setOnHand(newOnHand);
        StockLevel saved = stockLevelRepository.save(stock);

        StockMovement movement = new StockMovement(
                UUID.randomUUID(),
                saved,
                req.delta(),
                req.reason() != null ? req.reason() : "MANUAL_ADJUSTMENT",
                req.refId()
        );
        stockMovementRepository.save(movement);

        return toDto(saved);
    }

    /**
     * Critical Concurrency Method:
     * Reserves stock using atomic conditional update AND optimistic locking version bump.
     * Retries up to 3 times on contention. If capacity is insufficient, throws InsufficientStockException.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public ReserveStockResponse reserveStock(ReserveStockRequest req) {
        List<ReservationItemResultDto> itemResults = new ArrayList<>();
        List<Reservation> createdReservations = new ArrayList<>();

        for (OrderItemRequest item : req.items()) {
            boolean reserved = attemptReserveItem(req.orderId(), item.productId(), item.qty(), itemResults, createdReservations);
            if (!reserved) {
                // Rollback any partially allocated reservations in this request
                for (Reservation r : createdReservations) {
                    stockLevelRepository.releaseStockConditional(r.getStockLevelId(), r.getQty());
                    r.setStatus(ReservationStatus.RELEASED);
                    reservationRepository.save(r);
                }
                publishKafkaEvent("inventory.rejected", Map.of(
                        "orderId", req.orderId().toString(),
                        "reason", "Insufficient stock for product " + item.productId()
                ));
                throw new InsufficientStockException("Insufficient available stock for product: " + item.productId() + " (requested: " + item.qty() + ")");
            }
        }

        publishKafkaEvent("inventory.reserved", Map.of(
                "orderId", req.orderId().toString(),
                "itemCount", createdReservations.size()
        ));

        return new ReserveStockResponse(req.orderId(), true, itemResults, "Stock reserved successfully");
    }

    private boolean attemptReserveItem(UUID orderId, UUID productId, int qty,
                                       List<ReservationItemResultDto> itemResults,
                                       List<Reservation> createdReservations) {
        int maxRetries = 3;
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            List<StockLevel> stocks = stockLevelRepository.findByProductId(productId);
            if (stocks.isEmpty()) {
                return false;
            }

            // Find stock level with available capacity
            StockLevel targetStock = null;
            for (StockLevel sl : stocks) {
                if (sl.getAvailable() >= qty) {
                    targetStock = sl;
                    break;
                }
            }

            if (targetStock == null) {
                return false;
            }

            // Execute atomic conditional update with check (on_hand - reserved >= qty)
            int updatedRows = stockLevelRepository.reserveStockConditional(targetStock.getId(), qty);
            if (updatedRows > 0) {
                Reservation reservation = new Reservation(
                        UUID.randomUUID(),
                        orderId,
                        productId,
                        targetStock.getWarehouse(),
                        qty,
                        ReservationStatus.ACTIVE
                );
                Reservation savedRes = reservationRepository.save(reservation);
                createdReservations.add(savedRes);
                itemResults.add(new ReservationItemResultDto(productId, targetStock.getWarehouse().getId(), qty, true));

                // Check low stock threshold
                StockLevel reloaded = stockLevelRepository.findById(targetStock.getId()).orElse(targetStock);
                if (reloaded.getAvailable() <= reloaded.getLowStockThreshold()) {
                    publishKafkaEvent("inventory.low-stock", Map.of(
                            "productId", productId.toString(),
                            "warehouseId", targetStock.getWarehouse().getId().toString(),
                            "available", reloaded.getAvailable(),
                            "threshold", reloaded.getLowStockThreshold()
                    ));
                }
                return true;
            }

            // Contention occurred; back off briefly and retry
            try {
                Thread.sleep(10 * attempt);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                return false;
            }
        }
        return false;
    }

    @Transactional
    public ReleaseStockResponse releaseStock(ReleaseStockRequest req) {
        List<Reservation> activeReservations = reservationRepository.findByOrderIdAndStatus(req.orderId(), ReservationStatus.ACTIVE);
        int count = 0;
        for (Reservation res : activeReservations) {
            stockLevelRepository.findByWarehouseIdAndProductId(res.getWarehouse().getId(), res.getProductId())
                    .ifPresent(stock -> {
                        stockLevelRepository.releaseStockConditional(stock.getId(), res.getQty());
                        StockMovement movement = new StockMovement(
                                UUID.randomUUID(),
                                stock,
                                res.getQty(),
                                "ORDER_CANCELLED_RELEASE",
                                req.orderId().toString()
                        );
                        stockMovementRepository.save(movement);
                    });

            res.setStatus(ReservationStatus.RELEASED);
            reservationRepository.save(res);
            count++;
        }

        publishKafkaEvent("inventory.released", Map.of(
                "orderId", req.orderId().toString(),
                "releasedCount", count
        ));

        return new ReleaseStockResponse(req.orderId(), count, "Reservations released successfully");
    }

    private void publishKafkaEvent(String topic, Map<String, Object> payload) {
        if (kafkaTemplate != null) {
            try {
                kafkaTemplate.send(topic, payload.get("orderId") != null ? payload.get("orderId").toString() : UUID.randomUUID().toString(), payload);
            } catch (Exception e) {
                log.warn("Failed to publish Kafka event to topic {}: {}", topic, e.getMessage());
            }
        }
    }

    public StockLevelDto toDto(StockLevel s) {
        return new StockLevelDto(
                s.getId(),
                s.getWarehouse().getId(),
                s.getWarehouse().getCode(),
                s.getWarehouse().getName(),
                s.getProductId(),
                s.getOnHand(),
                s.getReserved(),
                s.getAvailable(),
                s.getLowStockThreshold(),
                s.getVersion(),
                s.getUpdatedAt()
        );
    }
}
""",

    # Controllers
    f"{BASE}/controller/WarehouseController.java": """package com.foodplatform.inventory.controller;

import com.foodplatform.inventory.dto.CreateWarehouseRequest;
import com.foodplatform.inventory.dto.WarehouseDto;
import com.foodplatform.inventory.service.WarehouseService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/warehouses")
@Tag(name = "Warehouses", description = "Warehouse locations management")
public class WarehouseController {

    private final WarehouseService warehouseService;

    public WarehouseController(WarehouseService warehouseService) {
        this.warehouseService = warehouseService;
    }

    @GetMapping
    @Operation(summary = "List all warehouses")
    public ResponseEntity<List<WarehouseDto>> getAllWarehouses() {
        return ResponseEntity.ok(warehouseService.getAllWarehouses());
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get warehouse by ID")
    public ResponseEntity<WarehouseDto> getWarehouseById(@PathVariable UUID id) {
        return ResponseEntity.ok(warehouseService.getWarehouseById(id));
    }

    @PostMapping
    @Operation(summary = "Create warehouse")
    public ResponseEntity<WarehouseDto> createWarehouse(@Valid @RequestBody CreateWarehouseRequest request) {
        WarehouseDto created = warehouseService.createWarehouse(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
""",

    f"{BASE}/controller/InventoryController.java": """package com.foodplatform.inventory.controller;

import com.foodplatform.inventory.dto.*;
import com.foodplatform.inventory.service.InventoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/inventory")
@Tag(name = "Inventory", description = "Stock levels and reservations management")
public class InventoryController {

    private final InventoryService inventoryService;

    public InventoryController(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    @GetMapping("/{productId}")
    @Operation(summary = "Get stock across all warehouses for a product")
    public ResponseEntity<List<StockLevelDto>> getStockByProduct(@PathVariable UUID productId) {
        return ResponseEntity.ok(inventoryService.getProductStock(productId));
    }

    @PostMapping("/adjust")
    @Operation(summary = "Adjust warehouse stock level (WAREHOUSE_OPERATOR+)")
    public ResponseEntity<StockLevelDto> adjustStock(@Valid @RequestBody AdjustStockRequest request) {
        return ResponseEntity.ok(inventoryService.adjustStock(request));
    }

    @PostMapping("/reserve")
    @Operation(summary = "Reserve stock for an order")
    public ResponseEntity<ReserveStockResponse> reserveStock(@Valid @RequestBody ReserveStockRequest request) {
        return ResponseEntity.ok(inventoryService.reserveStock(request));
    }

    @PostMapping("/release")
    @Operation(summary = "Release reserved stock for an order")
    public ResponseEntity<ReleaseStockResponse> releaseStock(@Valid @RequestBody ReleaseStockRequest request) {
        return ResponseEntity.ok(inventoryService.releaseStock(request));
    }
}
""",

    # Kafka Event Listener
    f"{BASE}/event/InventoryEventListener.java": """package com.foodplatform.inventory.event;

import com.foodplatform.inventory.dto.OrderItemRequest;
import com.foodplatform.inventory.dto.ReleaseStockRequest;
import com.foodplatform.inventory.dto.ReserveStockRequest;
import com.foodplatform.inventory.service.InventoryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Component
public class InventoryEventListener {

    private static final Logger log = LoggerFactory.getLogger(InventoryEventListener.class);

    private final InventoryService inventoryService;

    public InventoryEventListener(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    @KafkaListener(topics = "order.created", groupId = "inventory-service-group")
    public void handleOrderCreated(Map<String, Object> message) {
        try {
            log.info("Received order.created event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> items = (List<Map<String, Object>>) message.get("items");

            if (items != null && !items.isEmpty()) {
                List<OrderItemRequest> orderItems = items.stream().map(i -> new OrderItemRequest(
                        UUID.fromString(i.get("productId").toString()),
                        Integer.parseInt(i.get("qty").toString())
                )).toList();

                inventoryService.reserveStock(new ReserveStockRequest(orderId, orderItems));
            }
        } catch (Exception e) {
            log.warn("Failed to process order.created in inventory-service: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "order.cancelled", groupId = "inventory-service-group")
    public void handleOrderCancelled(Map<String, Object> message) {
        try {
            log.info("Received order.cancelled event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            inventoryService.releaseStock(new ReleaseStockRequest(orderId));
        } catch (Exception e) {
            log.warn("Failed to process order.cancelled in inventory-service: {}", e.getMessage());
        }
    }
}
""",

    # OpenAPI Config
    f"{BASE}/config/OpenApiConfig.java": """package com.foodplatform.inventory.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI inventoryOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Inventory Service API")
                        .description("Warehouses, stock levels, atomic reservations, and stock movements API")
                        .version("1.0.0"));
    }
}
"""
}

for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

print("All inventory-service source files written successfully.")
