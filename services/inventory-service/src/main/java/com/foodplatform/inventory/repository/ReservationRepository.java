package com.foodplatform.inventory.repository;

import com.foodplatform.inventory.domain.Reservation;
import com.foodplatform.inventory.domain.ReservationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReservationRepository extends JpaRepository<Reservation, UUID> {
    List<Reservation> findByOrderId(UUID orderId);
    List<Reservation> findByOrderIdAndStatus(UUID orderId, ReservationStatus status);
}
