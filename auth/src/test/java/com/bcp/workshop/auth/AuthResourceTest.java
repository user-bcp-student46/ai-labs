package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import jakarta.ws.rs.core.Response;
import org.junit.jupiter.api.Test;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class AuthResourceTest {
    private static final String TEST_USERNAME = "local'quote";
    private static final String TEST_PASSWORD = "LocalTestPassword123!";
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"))
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("debug", is("authenticated-with-legacy-flow"));
    }

    @Test
    void healthEndpointReportsUp() {
        given()
                .when().get("/q/health")
                .then()
                .statusCode(200)
                .body("status", is("UP"));
    }

    @Test
    void healthEndpointReportsNoChecksWhenNoneAreRegistered() {
        given()
                .when().get("/q/health")
                .then()
                .statusCode(200)
                .body("checks.size()", is(0));
    }

    @Test
    void rejectsNullLoginRequest() {
        given()
                .contentType("application/json")
                .body("null")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    @Test
    void rejectsMissingUsername() {
        given()
                .contentType("application/json")
                .body(Map.of("password", "Workshop123!"))
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsBlankUsername() {
        given()
                .contentType("application/json")
                .body(Map.of("username", "  ", "password", "Workshop123!"))
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsMissingPassword() {
        given()
                .contentType("application/json")
                .body(Map.of("username", "student"))
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsBlankPassword() {
        given()
                .contentType("application/json")
                .body(Map.of("username", "student", "password", "  "))
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsInvalidCredentials() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"IncorrectLocalPassword\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user student or password"));
    }

    @Test
    void reportsUnexpectedExceptionFromDatabase() {
        AuthResource resource = new AuthResource();
        resource.database = new LegacyDatabase() {
            @Override
            public UserRecord findByCredentials(String username, String password) {
                throw new IllegalStateException("database unavailable");
            }
        };
        LoginRequest request = new LoginRequest();
        request.username = "student";
        request.password = "Workshop123!";

        Response response = resource.login(request);

        assertEquals(500, response.getStatus());
        assertEquals(Map.of(
                "message", "database unavailable",
                "exception", IllegalStateException.class.getName()), response.getEntity());
    }

    @Test
    void usesFallbackMessageWhenExceptionHasNoMessage() {
        AuthResource resource = new AuthResource();
        resource.database = new LegacyDatabase() {
            @Override
            public UserRecord findByCredentials(String username, String password) {
                throw new IllegalStateException();
            }
        };
        LoginRequest request = new LoginRequest();
        request.username = "student";
        request.password = "Workshop123!";

        Response response = resource.login(request);

        assertEquals(500, response.getStatus());
        assertEquals(Map.of(
                "message", "Unknown error",
                "exception", IllegalStateException.class.getName()), response.getEntity());
    }

    @Test
    void storesSeededPasswordAsSaltedHash() throws SQLException {
        initializeDatabase();

        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(
                     "SELECT password_hash FROM legacy_users WHERE username = ?")) {
            statement.setString(1, "student");
            try (ResultSet result = statement.executeQuery()) {
                if (result.next()) {
                    String passwordHash = result.getString("password_hash");
                    assertNotEquals("Workshop123!", passwordHash);
                    assertTrue(PasswordHasher.matches("Workshop123!", passwordHash));
                } else {
                    throw new AssertionError("Workshop user was not seeded");
                }
            }
        }
    }

    @Test
    void logsInWithUsernameContainingQuote() throws SQLException {
        initializeDatabase();
        deleteQuotedUser();
        try {
            insertQuotedUser();

            given()
                    .contentType("application/json")
                    .body(Map.of("username", TEST_USERNAME, "password", TEST_PASSWORD))
                    .when().post("/auth/login")
                    .then()
                    .statusCode(200)
                    .body("user.username", is(TEST_USERNAME))
                    .body("token", notNullValue());
        } finally {
            deleteQuotedUser();
        }
    }

    private void initializeDatabase() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200);
    }

    private void insertQuotedUser() throws SQLException {
        String sql = "INSERT INTO legacy_users(username,password_hash,display_name,role) VALUES (?, ?, ?, ?)";
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, TEST_USERNAME);
            statement.setString(2, PasswordHasher.hash(TEST_PASSWORD));
            statement.setString(3, "Local Quote Test User");
            statement.setString(4, "STUDENT");
            statement.executeUpdate();
        }
    }

    private void deleteQuotedUser() throws SQLException {
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement("DELETE FROM legacy_users WHERE username = ?")) {
            statement.setString(1, TEST_USERNAME);
            statement.executeUpdate();
        }
    }
}
