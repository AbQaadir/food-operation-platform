package com.foodplatform.identity.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleResourceNotFound(ResourceNotFoundException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://foodplatform.com/errors/not-found"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(UserAlreadyExistsException.class)
    public ProblemDetail handleUserAlreadyExists(UserAlreadyExistsException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle("User Conflict");
        problem.setType(URI.create("https://foodplatform.com/errors/conflict"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(InvalidCredentialsException.class)
    public ProblemDetail handleInvalidCredentials(InvalidCredentialsException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.UNAUTHORIZED, ex.getMessage());
        problem.setTitle("Authentication Failed");
        problem.setType(URI.create("https://foodplatform.com/errors/unauthorized"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidationException(MethodArgumentNotValidException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        problem.setTitle("Bad Request");
        problem.setType(URI.create("https://foodplatform.com/errors/validation-error"));

        Map<String, String> errors = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            errors.put(error.getField(), error.getDefaultMessage());
        }
        problem.setProperty("errors", errors);
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneralException(Exception ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, ex.getMessage());
        problem.setTitle("Internal Server Error");
        problem.setType(URI.create("https://foodplatform.com/errors/internal"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    private String getCorrelationId(HttpServletRequest request) {
        String correlationId = request.getHeader("X-Correlation-Id");
        return correlationId != null ? correlationId : "unknown";
    }
}
