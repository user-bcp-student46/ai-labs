package com.bcp.workshop.auth;

import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

@ApplicationScoped
public class LegacyDatabase {
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");
    private static final String USERS_TABLE = "legacy_users";
    private static final String MIGRATION_TABLE = "legacy_users_hashed";
    private static final String STUDENT_USERNAME = "student";
    private static final String STUDENT_PASSWORD = "Workshop123!";
    private static final String TRAINER_USERNAME = "trainer";
    private static final String TRAINER_PASSWORD = "Trainer123!";

    @PostConstruct
    void initialize() {
        try {
            Files.createDirectories(Path.of("data"));
            try (Connection connection = DriverManager.getConnection(DB_URL)) {
                connection.setAutoCommit(false);
                migrateSchema(connection);
                seedDefaultUsers(connection);
                connection.commit();
            }
        } catch (Exception error) {
            error.printStackTrace();
        }
    }

    static void migrateSchema(Connection connection) throws Exception {
        if (!tableExists(connection, USERS_TABLE)) {
            createUsersTable(connection, USERS_TABLE);
            return;
        }

        boolean hasPlaintextPassword = hasColumn(connection, USERS_TABLE, "password");
        boolean hasPasswordHash = hasColumn(connection, USERS_TABLE, "password_hash");
        if (hasPasswordHash && !hasPlaintextPassword) {
            return;
        }
        if (!hasPlaintextPassword || hasPasswordHash) {
            throw new IllegalStateException("Unsupported legacy_users schema");
        }

        migratePlaintextPasswords(connection);
    }

    private static boolean tableExists(Connection connection, String tableName) throws Exception {
        String sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?";
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, tableName);
            try (ResultSet result = statement.executeQuery()) {
                return result.next();
            }
        }
    }

    private static boolean hasColumn(Connection connection, String tableName, String columnName) throws Exception {
        try (Statement statement = connection.createStatement();
             ResultSet columns = statement.executeQuery("PRAGMA table_info(" + tableName + ")")) {
            while (columns.next()) {
                if (columnName.equals(columns.getString("name"))) {
                    return true;
                }
            }
        }
        return false;
    }

    private static void createUsersTable(Connection connection, String tableName) throws Exception {
        String sql = "CREATE TABLE " + tableName + " (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                + "username TEXT UNIQUE, password_hash TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)";
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate(sql);
        }
    }

    private static void migratePlaintextPasswords(Connection connection) throws Exception {
        createUsersTable(connection, MIGRATION_TABLE);
        String selectSql = "SELECT id, username, password, display_name, role FROM " + USERS_TABLE;
        String insertSql = "INSERT INTO " + MIGRATION_TABLE
                + "(id, username, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)";
        try (Statement selectStatement = connection.createStatement();
             ResultSet users = selectStatement.executeQuery(selectSql);
             PreparedStatement insertStatement = connection.prepareStatement(insertSql)) {
            while (users.next()) {
                insertStatement.setLong(1, users.getLong("id"));
                insertStatement.setString(2, users.getString("username"));
                insertStatement.setString(3, PasswordHasher.hash(users.getString("password")));
                insertStatement.setString(4, users.getString("display_name"));
                insertStatement.setString(5, users.getString("role"));
                insertStatement.executeUpdate();
            }
        }

        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate("DROP TABLE " + USERS_TABLE);
            statement.executeUpdate("ALTER TABLE " + MIGRATION_TABLE + " RENAME TO " + USERS_TABLE);
        }
    }

    private static void seedDefaultUsers(Connection connection) throws Exception {
        seedUser(connection, STUDENT_USERNAME, STUDENT_PASSWORD, "Workshop Student", "STUDENT");
        seedUser(connection, TRAINER_USERNAME, TRAINER_PASSWORD, "Workshop Trainer", "TRAINER");
    }

    private static void seedUser(Connection connection, String username, String password,
                                 String displayName, String role) throws Exception {
        String sql = "INSERT OR IGNORE INTO legacy_users(username, password_hash, display_name, role) VALUES (?, ?, ?, ?)";
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            statement.setString(2, PasswordHasher.hash(password));
            statement.setString(3, displayName);
            statement.setString(4, role);
            statement.executeUpdate();
        }
    }

    public UserRecord findByCredentials(String username, String password) {
        String sql = "SELECT id, username, password_hash, display_name, role FROM legacy_users WHERE username=?";
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            try (ResultSet result = statement.executeQuery()) {
                if (!result.next() || !PasswordHasher.matches(password, result.getString("password_hash"))) {
                    return null;
                }
                return new UserRecord(result.getLong("id"), result.getString("username"), result.getString("display_name"), result.getString("role"));
            }
        } catch (Exception error) {
            error.printStackTrace();
        }
        return null;
    }
}
