package com.foodplatform.order;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.client.ProductClient;
import com.foodplatform.order.domain.OrderStatus;
import com.foodplatform.order.domain.OutboxEvent;
import com.foodplatform.order.dto.CreateOrderItemRequest;
import com.foodplatform.order.dto.CreateOrderRequest;
import com.foodplatform.order.dto.OrderDto;
import com.foodplatform.order.repository.IdempotencyRecordRepository;
import com.foodplatform.order.repository.OrderItemRepository;
import com.foodplatform.order.repository.OrderRepository;
import com.foodplatform.order.repository.OutboxEventRepository;
import com.foodplatform.order.service.IdempotencyService;
import com.foodplatform.order.service.OrderService;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SpecVersion;
import com.networknt.schema.ValidationMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.context.ActiveProfiles;

import java.io.File;
import java.io.FileInputStream;
import java.math.BigDecimal;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;

@SpringBootTest
@ActiveProfiles("test")
class OrderServiceIntegrationTest {

    @Autowired
    private OrderService orderService;

    @Autowired
    private IdempotencyService idempotencyService;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private OrderItemRepository orderItemRepository;

    @Autowired
    private OutboxEventRepository outboxEventRepository;

    @Autowired
    private IdempotencyRecordRepository idempotencyRecordRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private KafkaTemplate<String, Object> kafkaTemplate;

    @MockBean
    private ProductClient productClient;

    private UUID customerId;
    private UUID productId;

    @BeforeEach
    void setUp() {
        outboxEventRepository.deleteAll();
        orderItemRepository.deleteAll();
        orderRepository.deleteAll();
        idempotencyRecordRepository.deleteAll();

        customerId = UUID.randomUUID();
        productId = UUID.randomUUID();

        Mockito.when(productClient.fetchProduct(any())).thenReturn(
                new ProductClient.ProductInfo(productId, "FOOD-TEST-01", "Test Organic Spinach", new BigDecimal("12.50"), true)
        );
    }

    @Test
    @DisplayName("Transactional Outbox: order creation writes both order and outbox_event in single transaction")
    void testCreateOrderWithTransactionalOutbox() throws Exception {
        CreateOrderRequest request = new CreateOrderRequest(
                customerId,
                "USD",
                List.of(new CreateOrderItemRequest(productId, "FOOD-TEST-01", "Test Organic Spinach", new BigDecimal("12.50"), 2))
        );

        OrderDto created = orderService.createOrder(request);

        assertNotNull(created.id());
        assertEquals(OrderStatus.PENDING, created.status());
        assertEquals(new BigDecimal("25.00"), created.totalAmount());
        assertEquals(1, created.items().size());

        // Verify Outbox Event exists
        List<OutboxEvent> outboxList = outboxEventRepository.findAll();
        assertEquals(1, outboxList.size(), "Exactly 1 outbox event must be written");
        OutboxEvent outbox = outboxList.get(0);
        assertEquals("Order", outbox.getAggregateType());
        assertEquals(created.id().toString(), outbox.getAggregateId());
        assertEquals("order.created", outbox.getType());

        // Validate event payload against JSON Schema contract
        File schemaFile = new File("../../contracts/events/order.created.schema.json");
        if (schemaFile.exists()) {
            JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
            try (FileInputStream fis = new FileInputStream(schemaFile)) {
                JsonSchema schema = factory.getSchema(fis);
                JsonNode payloadNode = objectMapper.readTree(outbox.getPayload());
                Set<ValidationMessage> errors = schema.validate(payloadNode);
                assertTrue(errors.isEmpty(), "Outbox payload must validate against order.created schema: " + errors);
            }
        }
    }

    @Test
    @DisplayName("Idempotency: saving and retrieving response via Redis / DB")
    void testIdempotencyHandling() {
        String key = "test-idempotency-key-" + UUID.randomUUID();
        String json = "{\"orderId\":\"test-order\"}";

        assertFalse(idempotencyService.getCachedResponse(key).isPresent());

        idempotencyService.saveResponse(key, 201, json);

        var cached = idempotencyService.getCachedResponse(key);
        assertTrue(cached.isPresent());
        assertEquals(201, cached.get().statusCode());
        assertEquals(json, cached.get().body());
    }

    @Test
    @DisplayName("State Machine: cancel an order sets status to CANCELLED and generates outbox event")
    void testCancelOrder() {
        CreateOrderRequest request = new CreateOrderRequest(
                customerId,
                "USD",
                List.of(new CreateOrderItemRequest(productId, "FOOD-TEST-01", "Test Organic Spinach", new BigDecimal("12.50"), 1))
        );

        OrderDto created = orderService.createOrder(request);
        OrderDto cancelled = orderService.cancelOrder(created.id(), "Customer changed mind");

        assertEquals(OrderStatus.CANCELLED, cancelled.status());
        assertEquals("Customer changed mind", cancelled.cancelReason());

        List<OutboxEvent> events = outboxEventRepository.findAll();
        boolean hasCancelEvent = events.stream().anyMatch(e -> "order.cancelled".equals(e.getType()));
        assertTrue(hasCancelEvent, "Order cancellation must generate an order.cancelled outbox event");
    }
}
