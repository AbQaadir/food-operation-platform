package com.foodplatform.inventory;

import com.foodplatform.inventory.domain.StockLevel;
import com.foodplatform.inventory.domain.Warehouse;
import com.foodplatform.inventory.dto.OrderItemRequest;
import com.foodplatform.inventory.dto.ReserveStockRequest;
import com.foodplatform.inventory.dto.ReserveStockResponse;
import com.foodplatform.inventory.exception.InsufficientStockException;
import com.foodplatform.inventory.repository.ReservationRepository;
import com.foodplatform.inventory.repository.StockLevelRepository;
import com.foodplatform.inventory.repository.StockMovementRepository;
import com.foodplatform.inventory.repository.WarehouseRepository;
import com.foodplatform.inventory.service.InventoryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest
@ActiveProfiles("test")
class InventoryConcurrencyTest {

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private WarehouseRepository warehouseRepository;

    @Autowired
    private StockLevelRepository stockLevelRepository;

    @Autowired
    private ReservationRepository reservationRepository;

    @Autowired
    private StockMovementRepository stockMovementRepository;

    @MockBean
    private KafkaTemplate<String, Object> kafkaTemplate;

    private Warehouse warehouse;
    private UUID productId;
    private StockLevel stockLevel;

    @BeforeEach
    void setUp() {
        reservationRepository.deleteAll();
        stockMovementRepository.deleteAll();
        stockLevelRepository.deleteAll();
        warehouseRepository.deleteAll();

        warehouse = new Warehouse(UUID.randomUUID(), "WH-CONCURRENCY", "Concurrency Test Warehouse", "Sector 7G");
        warehouseRepository.save(warehouse);

        productId = UUID.randomUUID();
        // 10 units on-hand, 0 reserved -> exactly 10 units available
        stockLevel = new StockLevel(UUID.randomUUID(), warehouse, productId, 10, 0, 5);
        stockLevelRepository.save(stockLevel);
    }

    @Test
    @DisplayName("50 concurrent threads compete for 10 units of stock -> exactly 10 succeed, 40 fail (409)")
    void testConcurrentReservationsNeverOversell() throws InterruptedException {
        int threadCount = 50;
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        CountDownLatch readyLatch = new CountDownLatch(threadCount);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(threadCount);

        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger conflictCount = new AtomicInteger(0);
        AtomicInteger unexpectedErrorCount = new AtomicInteger(0);

        for (int i = 0; i < threadCount; i++) {
            executor.submit(() -> {
                readyLatch.countDown();
                try {
                    startLatch.await(); // wait until all 50 threads are queued

                    UUID orderId = UUID.randomUUID();
                    ReserveStockRequest req = new ReserveStockRequest(
                            orderId,
                            List.of(new OrderItemRequest(productId, 1))
                    );

                    ReserveStockResponse response = inventoryService.reserveStock(req);
                    if (response.success()) {
                        successCount.incrementAndGet();
                    }
                } catch (InsufficientStockException e) {
                    conflictCount.incrementAndGet();
                } catch (Exception e) {
                    unexpectedErrorCount.incrementAndGet();
                } finally {
                    doneLatch.countDown();
                }
            });
        }

        readyLatch.await(5, TimeUnit.SECONDS);
        startLatch.countDown(); // FIRE all 50 threads simultaneously
        doneLatch.await(15, TimeUnit.SECONDS);
        executor.shutdown();

        assertEquals(0, unexpectedErrorCount.get(), "No unexpected errors should occur");
        assertEquals(10, successCount.get(), "Exactly 10 threads must succeed in reserving stock");
        assertEquals(40, conflictCount.get(), "Exactly 40 threads must receive InsufficientStockException (409)");

        StockLevel finalStock = stockLevelRepository.findById(stockLevel.getId()).orElseThrow();
        assertEquals(10, finalStock.getOnHand(), "On-hand stock must remain 10");
        assertEquals(10, finalStock.getReserved(), "Reserved stock must equal 10");
        assertEquals(0, finalStock.getAvailable(), "Available stock must be exactly 0 (no oversell)");
    }
}
