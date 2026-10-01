package com.foodplatform.order.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.time.Instant;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.NOT_FOUND, "Resource Not Found", ex.getMessage(), "not-found", request);
    }

    @ExceptionHandler(InvalidOrderStateException.class)
    public ProblemDetail handleInvalidState(InvalidOrderStateException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Invalid Order State", ex.getMessage(), "invalid-state", request);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex, WebRequest request) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Validation Error", detail, "validation-error", request);
    }

    @ExceptionHandler(com.foodplatform.order.controller.MissingIdempotencyKeyException.class)
    public ProblemDetail handleMissingIdempotencyKey(com.foodplatform.order.controller.MissingIdempotencyKeyException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Missing Required Header", ex.getMessage(), "missing-header", request);
    }

    @ExceptionHandler(org.springframework.web.bind.MissingRequestHeaderException.class)
    public ProblemDetail handleMissingHeader(org.springframework.web.bind.MissingRequestHeaderException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Missing Required Header", ex.getMessage(), "missing-header", request);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail handleIllegalArgument(IllegalArgumentException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Bad Request", ex.getMessage(), "bad-request", request);
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneric(Exception ex, WebRequest request) {
        log.error("Unhandled exception in order-service", ex);
        return buildProblemDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", ex.getMessage(), "internal", request);
    }

    private ProblemDetail buildProblemDetail(HttpStatus status, String title, String detail, String typeCode, WebRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(title);
        pd.setType(URI.create("https://foodplatform.com/errors/" + typeCode));
        pd.setProperty("timestamp", Instant.now());
        if (request instanceof ServletWebRequest swr) {
            pd.setInstance(URI.create(swr.getRequest().getRequestURI()));
            String correlationId = swr.getHeader("X-Correlation-Id");
            if (correlationId != null) {
                pd.setProperty("correlationId", correlationId);
            }
        }
        return pd;
    }
}
