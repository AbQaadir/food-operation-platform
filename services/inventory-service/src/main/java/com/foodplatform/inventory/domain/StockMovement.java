package com.foodplatform.inventory.domain;

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
