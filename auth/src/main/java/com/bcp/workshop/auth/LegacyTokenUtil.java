package com.bcp.workshop.auth;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import org.eclipse.microprofile.config.ConfigProvider;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

public final class LegacyTokenUtil {
    private static final String SIGNING_SECRET_PROPERTY = "auth.token.secret";
    private static final int MINIMUM_SECRET_BYTES = 32;
    public static final int TOKEN_LIFETIME_SECONDS = (int) Duration.ofHours(1).getSeconds();

    private LegacyTokenUtil() {}

    public static String create(String username, String role) {
        String signingSecret = ConfigProvider.getConfig()
                .getOptionalValue(SIGNING_SECRET_PROPERTY, String.class)
                .orElse(null);
        return create(username, role, signingSecret);
    }

    static String create(String username, String role, String signingSecret) {
        if (signingSecret == null || signingSecret.getBytes(StandardCharsets.UTF_8).length < MINIMUM_SECRET_BYTES) {
            throw new IllegalStateException("AUTH_TOKEN_SECRET must contain at least 32 bytes");
        }

        Instant issuedAt = Instant.now();
        return JWT.create()
                .withSubject(username)
                .withClaim("role", role)
                .withIssuedAt(Date.from(issuedAt))
                .withExpiresAt(Date.from(issuedAt.plusSeconds(TOKEN_LIFETIME_SECONDS)))
                .sign(Algorithm.HMAC256(signingSecret));
    }
}
