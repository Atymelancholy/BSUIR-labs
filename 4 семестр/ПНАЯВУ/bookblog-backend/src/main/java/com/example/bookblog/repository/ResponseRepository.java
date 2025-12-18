package com.example.bookblog.repository;

import com.example.bookblog.entity.Response;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ResponseRepository extends JpaRepository<Response, Long> {
    List<Response> findByUserId(Long userId);

    List<Response> findByBookId(Long bookId);
}