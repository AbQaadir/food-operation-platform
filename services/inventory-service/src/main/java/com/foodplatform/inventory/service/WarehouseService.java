package com.foodplatform.inventory.service;

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
