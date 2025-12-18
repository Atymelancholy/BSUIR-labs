package com.example.bookblog.repository;

import com.example.bookblog.entity.Book;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;


@Repository
public interface BookRepository extends JpaRepository<Book, Long> {
    Optional<Book> findById(Long id);

    boolean existsByTitleAndAuthor(String title, String author);

    List<Book> findByCategories_Id(Long categoryId);
}
