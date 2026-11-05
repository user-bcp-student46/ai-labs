package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.CoreMatchers.nullValue;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class AuthResourceTest {
    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("token", notNullValue());
    }

    // --- Caracterización H-AUTH-01: protegen el contrato de POST /auth/login
    // descrito en openspec/changes/h-auth-01-parameterized-login-query/specs/auth-login/spec.md
    // antes de tocar LegacyDatabase.findByCredentials. ---

    @Test
    void logsInWithTrainerUser() {
        // Protege el login válido del rol trainer (200, token no nulo).
        given()
                .contentType("application/json")
                .body("{\"username\":\"trainer\",\"password\":\"Trainer123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("trainer"))
                .body("token", notNullValue());
    }

    @Test
    void rejectsIncorrectPasswordForStudent() {
        // Protege que una contraseña incorrecta siga respondiendo 401 sin token.
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"wrong-password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsNonexistentUser() {
        // Protege que un usuario inexistente siga respondiendo 401 sin token.
        given()
                .contentType("application/json")
                .body("{\"username\":\"ghost\",\"password\":\"whatever\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsBlankUsername() {
        // Protege el 400 "Username is required" cuando el usuario llega en blanco.
        given()
                .contentType("application/json")
                .body("{\"username\":\"\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsBlankPassword() {
        // Protege el 400 "Password is required" cuando la contraseña llega en blanco.
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsSqlInjectionInUsernameWithoutToken() {
        // Documenta el comportamiento frente a inyección SQL en username (H-AUTH-01);
        // se espera 401 sin token tras la corrección, pero hoy puede fallar en rojo.
        given()
                .contentType("application/json")
                .body("{\"username\":\"' OR '1'='1\",\"password\":\"anything\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsSqlInjectionInPasswordWithoutToken() {
        // Igual que el anterior, con el vector de inyección en password.
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"' OR '1'='1\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsSqlCommentInUsernameWithoutToken() {
        // Variante con comentario SQL (--) para cerrar la cláusula WHERE.
        given()
                .contentType("application/json")
                .body("{\"username\":\"student'--\",\"password\":\"anything\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void acceptsBenignApostropheWithout500() {
        // Protege que una comilla simple benigna (dato de negocio, no ataque) siga devolviendo 401 y no 500.
        given()
                .contentType("application/json")
                .body("{\"username\":\"o'brien\",\"password\":\"anything\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401);
    }
}
