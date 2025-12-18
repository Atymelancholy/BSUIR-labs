package com.example.bookblog.cache;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class InMemoryCache<K, V> {
    private static final Logger logger = LoggerFactory.getLogger(InMemoryCache.class);
    private static final int MAX_SIZE = 2;
    private static final Duration TTL = Duration.ofMinutes(10);

    private final Map<K, CacheEntry<V>> cache = new LinkedHashMap<>(MAX_SIZE, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, CacheEntry<V>> eldest) {
            boolean shouldRemove = size() > MAX_SIZE || eldest.getValue().isExpired();
            if (size() > MAX_SIZE) {
                logger.warn("Cache size exceeded max limit of {}."
                        + " Removing eldest entry.", MAX_SIZE);
            }
            return shouldRemove;
        }
    };

    public Optional<V> get(K key) {
        cleanUp();
        CacheEntry<V> entry = cache.get(key);
        if (entry == null || entry.isExpired()) {
            cache.remove(key);
            return Optional.empty();
        }
        return Optional.of(entry.value);
    }

    public V getOrCompute(K key, Supplier<V> supplier) {
        return get(key).orElseGet(() -> {
            V value = supplier.get();
            put(key, value);
            return value;
        });
    }

    public void put(K key, V value) {
        cleanUp();
        cache.put(key, new CacheEntry<>(value, Instant.now().plus(TTL)));
    }

    public void update(K key, V newValue) {
        if (cache.containsKey(key)) {
            cache.put(key, new CacheEntry<>(newValue, Instant.now().plus(TTL)));
        }
    }

    public void remove(K key) {
        cache.remove(key);
    }

    public void clear() {
        cache.clear();
    }

    private void cleanUp() {
        cache.entrySet().removeIf(entry -> entry.getValue().isExpired());
    }

    private static class CacheEntry<V> {
        private final V value;
        private final Instant expiryTime;

        CacheEntry(V value, Instant expiryTime) {
            this.value = value;
            this.expiryTime = expiryTime;
        }

        boolean isExpired() {
            return Instant.now().isAfter(expiryTime);
        }
    }
}
