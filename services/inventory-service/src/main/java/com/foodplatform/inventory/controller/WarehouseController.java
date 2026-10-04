package com.foodplatform.inventory.controller;

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
