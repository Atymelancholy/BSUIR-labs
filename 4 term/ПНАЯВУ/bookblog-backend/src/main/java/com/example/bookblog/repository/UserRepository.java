package com.example.bookblog.repository;

import com.example.bookblog.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    User findByUsername(String username);

    @EntityGraph(attributePaths = {"responses", "categories"})
    Optional<User> findWithPostsAndGroupsById(Long id);

}
