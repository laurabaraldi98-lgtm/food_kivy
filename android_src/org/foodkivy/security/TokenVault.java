package org.foodkivy.security;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * Stores the refresh token on Android. Python calls this class through PyJNIus
 * because Android Keystore is accessed through the Android Java APIs.
 */
public final class TokenVault {
    private static final String KEYSTORE = "AndroidKeyStore";
    private static final String KEY_ALIAS = "food-kivy-refresh-key-v1";
    private static final String PREFERENCES = "food-kivy-secure-session";
    private static final String TOKEN_ENTRY = "refresh-token";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";

    private TokenVault() {
    }

    private static SharedPreferences preferences(Context context) {
        return context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE);
    }

    private static synchronized SecretKey getOrCreateKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(KEYSTORE);
        keyStore.load(null);

        if (keyStore.containsAlias(KEY_ALIAS)) {
            return (SecretKey) keyStore.getKey(KEY_ALIAS, null);
        }

        KeyGenerator generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            KEYSTORE
        );

        KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .build();

        generator.init(spec);
        return generator.generateKey();
    }

    private static SecretKey getExistingKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(KEYSTORE);
        keyStore.load(null);

        SecretKey key = (SecretKey) keyStore.getKey(KEY_ALIAS, null);

        if (key == null) {
            throw new GeneralSecurityException(
                "Stored token has no matching key"
            );
        }

        return key;
    }

    public static void save(Context context, String token) throws Exception {
        if (token == null || token.isEmpty()) {
            throw new IllegalArgumentException("Token is empty");
        }

        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());

        byte[] iv = cipher.getIV();
        byte[] encrypted = cipher.doFinal(
            token.getBytes(StandardCharsets.UTF_8)
        );

        String value =
            Base64.encodeToString(iv, Base64.NO_WRAP)
            + ":"
            + Base64.encodeToString(encrypted, Base64.NO_WRAP);

        boolean saved = preferences(context)
            .edit()
            .putString(TOKEN_ENTRY, value)
            .commit();

        if (!saved) {
            throw new IllegalStateException(
                "Encrypted token could not be saved"
            );
        }
    }

    public static String load(Context context) throws Exception {
        String value = preferences(context).getString(TOKEN_ENTRY, null);

        if (value == null) {
            return null;
        }

        int separator = value.indexOf(':');

        if (separator < 0 || separator != value.lastIndexOf(':')) {
            throw new GeneralSecurityException("Invalid encrypted token");
        }

        byte[] iv = Base64.decode(
            value.substring(0, separator),
            Base64.NO_WRAP
        );
        byte[] encrypted = Base64.decode(
            value.substring(separator + 1),
            Base64.NO_WRAP
        );

        if (iv.length != 12) {
            throw new GeneralSecurityException("Invalid encryption IV");
        }

        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(
            Cipher.DECRYPT_MODE,
            getExistingKey(),
            new GCMParameterSpec(128, iv)
        );

        byte[] decrypted = cipher.doFinal(encrypted);
        return new String(decrypted, StandardCharsets.UTF_8);
    }

    public static void delete(Context context) {
        boolean deleted = preferences(context)
            .edit()
            .remove(TOKEN_ENTRY)
            .commit();

        if (!deleted) {
            throw new IllegalStateException(
                "Encrypted token could not be deleted"
            );
        }
    }
}