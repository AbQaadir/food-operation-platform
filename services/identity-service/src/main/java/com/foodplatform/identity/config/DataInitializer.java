package com.foodplatform.identity.config;

import com.foodplatform.identity.domain.Role;
import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.UUID;

@Configuration
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public DataInitializer(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        seedUser("admin@foodplatform.com", "Admin123!", "Global Administrator", Role.ADMIN);
        seedUser("manager@foodplatform.com", "Manager123!", "Operations Manager", Role.MANAGER);
        seedUser("operator@foodplatform.com", "Operator123!", "Warehouse Operator", Role.WAREHOUSE_OPERATOR);
        seedUser("customer@foodplatform.com", "Customer123!", "Customer Account", Role.CUSTOMER);
    }

    private void seedUser(String email, String rawPassword, String fullName, Role role) {
        if (!userRepository.existsByEmailIgnoreCase(email)) {
            User user = new User(
                    UUID.randomUUID(),
                    email.toLowerCase(),
                    passwordEncoder.encode(rawPassword),
                    fullName,
                    role,
                    true
            );
            userRepository.save(user);
            log.info("Seeded default user: {} with role: {}", email, role);
        }
    }
}
