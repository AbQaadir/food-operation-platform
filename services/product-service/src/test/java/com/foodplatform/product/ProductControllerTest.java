package com.foodplatform.product;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.product.dto.CreateProductRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldCreateAndRetrieveProduct() throws Exception {
        CreateProductRequest request = new CreateProductRequest(
                "TEST-SKU-100",
                "Organic Sourdough Bread",
                "Fresh artisanal sourdough loaf",
                null,
                "loaf",
                new BigDecimal("6.50"),
                "USD",
                true
        );

        mockMvc.perform(post("/api/v1/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.sku").value("TEST-SKU-100"))
                .andExpect(jsonPath("$.name").value("Organic Sourdough Bread"))
                .andExpect(jsonPath("$.price").value(6.50));

        mockMvc.perform(get("/api/v1/products")
                        .param("q", "sourdough"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].sku").value("TEST-SKU-100"));
    }
}
