package com.foodplatform.order.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/** Thrown when POST /api/v1/orders is called without the mandatory Idempotency-Key header. */
@ResponseStatus(HttpStatus.BAD_REQUEST)
public class MissingIdempotencyKeyException extends RuntimeException {
    public MissingIdempotencyKeyException() {
        super("Missing required header: Idempotency-Key");
    }
}
