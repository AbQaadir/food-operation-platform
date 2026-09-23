package com.foodplatform.inventory.service;

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
                    stockLevelRepository.findByWarehouseIdAndProductId(r.getWarehouse().getId(), r.getProductId())
                            .ifPresent(stock -> stockLevelRepository.releaseStockConditional(stock.getId(), r.getQty()));
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
