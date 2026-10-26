package com.bcp.workshop.auth;

import io.quarkus.elytron.security.common.BcryptUtil;

public final class PasswordHasher {
    private PasswordHasher() {}

    public static String hash(String password) {
        return BcryptUtil.bcryptHash(password);
    }

    public static boolean matches(String password, String passwordHash) {
        return BcryptUtil.matches(password, passwordHash);
    }
}