package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class LegacyDatabaseTest {
    @Test
    void migratesLegacyPasswordsAndCanRunAgain() throws Exception {
        Class.forName("org.sqlite.JDBC");
        try (Connection connection = DriverManager.getConnection("jdbc:sqlite::memory:")) {
            createLegacyTable(connection);
            insertLegacyUser(connection);

            LegacyDatabase.migrateSchema(connection);
            assertMigratedPassword(connection);
            assertFalse(hasColumn(connection, "password"));

            LegacyDatabase.migrateSchema(connection);
            assertMigratedPassword(connection);
        }
    }

    private void createLegacyTable(Connection connection) throws Exception {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    + "username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)");
        }
    }

    private void insertLegacyUser(Connection connection) throws Exception {
        String sql = "INSERT INTO legacy_users(username, password, display_name, role) VALUES (?, ?, ?, ?)";
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, "legacy-student");
            statement.setString(2, "LegacyLocalPassword123!");
            statement.setString(3, "Legacy Student");
            statement.setString(4, "STUDENT");
            statement.executeUpdate();
        }
    }

    private void assertMigratedPassword(Connection connection) throws Exception {
        try (Statement statement = connection.createStatement();
             ResultSet result = statement.executeQuery(
                     "SELECT password_hash, role FROM legacy_users WHERE username='legacy-student'")) {
            assertTrue(result.next());
            String passwordHash = result.getString("password_hash");
            assertTrue(PasswordHasher.matches("LegacyLocalPassword123!", passwordHash));
            assertFalse("LegacyLocalPassword123!".equals(passwordHash));
            assertEquals("STUDENT", result.getString("role"));
        }
    }

    private boolean hasColumn(Connection connection, String columnName) throws Exception {
        try (Statement statement = connection.createStatement();
             ResultSet columns = statement.executeQuery("PRAGMA table_info(legacy_users)")) {
            while (columns.next()) {
                if (columnName.equals(columns.getString("name"))) {
                    return true;
                }
            }
        }
        return false;
    }
}