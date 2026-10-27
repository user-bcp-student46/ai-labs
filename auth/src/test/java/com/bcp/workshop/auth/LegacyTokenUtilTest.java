package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertThrows;

class LegacyTokenUtilTest {
    @Test
    void rejectsMissingSigningSecret() {
        assertThrows(IllegalStateException.class,
                () -> LegacyTokenUtil.create("student", "STUDENT", null));
    }

    @Test
    void rejectsSigningSecretShorterThanHmacMinimum() {
        assertThrows(IllegalStateException.class,
                () -> LegacyTokenUtil.create("student", "STUDENT", "short-test-key"));
    }
}