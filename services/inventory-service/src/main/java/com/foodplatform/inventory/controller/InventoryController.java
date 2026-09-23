package com.foodplatform.inventory.controller;

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
