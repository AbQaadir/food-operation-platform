package com.foodplatform.product.repository;

import com.foodplatform.product.domain.Product;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class ProductSpecifications {

    public static Specification<Product> withFilters(
            UUID categoryId,
            String query,
            BigDecimal minPrice,
            BigDecimal maxPrice,
            Boolean active
    ) {
        return (root, cq, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (categoryId != null) {
                predicates.add(cb.equal(root.get("categoryId"), categoryId));
            }

            if (query != null && !query.isBlank()) {
                String pattern = "%" + query.toLowerCase().trim() + "%";
                Predicate nameMatch = cb.like(cb.lower(root.get("name")), pattern);
                Predicate skuMatch = cb.like(cb.lower(root.get("sku")), pattern);
                Predicate descMatch = cb.like(cb.lower(root.get("description")), pattern);
                predicates.add(cb.or(nameMatch, skuMatch, descMatch));
            }

            if (minPrice != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("price"), minPrice));
            }

            if (maxPrice != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("price"), maxPrice));
            }

            if (active != null) {
                predicates.add(cb.equal(root.get("active"), active));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}
