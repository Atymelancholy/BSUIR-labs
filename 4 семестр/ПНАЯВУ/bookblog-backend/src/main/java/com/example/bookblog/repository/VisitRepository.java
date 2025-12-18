package com.example.bookblog.repository;

import com.example.bookblog.entity.Visit;
import java.time.LocalDateTime;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface VisitRepository extends JpaRepository<Visit, String> {
    @Modifying
    @Query("UPDATE Visit v SET v.count = v.count + 1, v.lastUpdated = :now WHERE v.url = :url")
    void incrementCount(@Param("url") String url, @Param("now") LocalDateTime now);

    Optional<Visit> findByUrl(String url);

    boolean existsByUrl(String url);
}