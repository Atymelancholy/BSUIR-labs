package com.example.bookblog.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "books")
public class Book {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String title;
    private String author;

    @JsonIgnore
    @OneToMany(mappedBy = "book",
            cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)

    private List<Response> responses = new ArrayList<>();

    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE }, fetch = FetchType.LAZY)
    @JoinTable(
            name = "book_category",
            joinColumns = @JoinColumn(name = "book_id"),
            inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    private Set<Category> categories = new HashSet<>();

    public Book() {}

    public Book(String title, String author) {
        this.title = title;
        this.author = author;
    }

    // Inside the Book class
    public void addCategory(Category category) {
        categories.add(category);
        category.getBooks().add(this);  // Ensure that the inverse relationship is maintained
    }

    public void removeCategory(Category category) {
        categories.remove(category);
        category.getBooks().remove(this);  // Remove the inverse relationship
    }


    public Set<Category> getCategories() {
        return categories;
    }

    public void setCategories(Set<Category> categories) {
        this.categories = categories;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public List<Response> getResponses() {
        return responses;
    }

    public void addResponse(Response response) {
        responses.add(response);
        response.setBook(this);
    }

    public void removeResponse(Response response) {
        responses.remove(response);
        response.setBook(null);
    }
}
