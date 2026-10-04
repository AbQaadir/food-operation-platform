package com.foodplatform.product.service;

import com.foodplatform.product.domain.Category;
import com.foodplatform.product.dto.CategoryDto;
import com.foodplatform.product.dto.CreateCategoryRequest;
import com.foodplatform.product.exception.DuplicateResourceException;
import com.foodplatform.product.exception.ResourceNotFoundException;
import com.foodplatform.product.repository.CategoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @Transactional(readOnly = true)
    public List<CategoryDto> getAllCategories() {
        return categoryRepository.findAll().stream()
                .map(this::toDto)
                .toList();
    }

    @Transactional(readOnly = true)
    public CategoryDto getCategoryById(UUID id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found with id: " + id));
        return toDto(category);
    }

    @Transactional
    public CategoryDto createCategory(CreateCategoryRequest request) {
        if (categoryRepository.existsByNameIgnoreCase(request.name())) {
            throw new DuplicateResourceException("Category already exists with name: " + request.name());
        }

        Category category = new Category(UUID.randomUUID(), request.name().trim(), request.parentId());
        Category saved = categoryRepository.save(category);
        return toDto(saved);
    }

    private CategoryDto toDto(Category category) {
        return new CategoryDto(
                category.getId(),
                category.getName(),
                category.getParentId(),
                category.getCreatedAt()
        );
    }
}
