package com.foodplatform.inventory.repository;

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
    @Query("UPDATE StockLevel s SET s.reserved = s.reserved + :qty, s.version = s.version + 1 " +
           "WHERE s.id = :id AND (s.onHand - s.reserved) >= :qty")
    int reserveStockConditional(@Param("id") UUID id, @Param("qty") int qty);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("UPDATE StockLevel s SET s.reserved = s.reserved - :qty, s.version = s.version + 1 " +
           "WHERE s.id = :id AND s.reserved >= :qty")
    int releaseStockConditional(@Param("id") UUID id, @Param("qty") int qty);
}
