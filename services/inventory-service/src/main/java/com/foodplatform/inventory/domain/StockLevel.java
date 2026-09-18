package com.foodplatform.inventory.domain;

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
