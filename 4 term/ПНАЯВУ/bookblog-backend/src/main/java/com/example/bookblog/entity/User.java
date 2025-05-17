package com.example.bookblog.entity;

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
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String username;
    private String password;


    @OneToMany(mappedBy = "user", cascade = { CascadeType.PERSIST, CascadeType.MERGE,
        CascadeType.REMOVE }, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<Response> responses = new ArrayList<>();

    public List<Response> getResponses() {
        return responses;
    }

    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE }, fetch = FetchType.LAZY)
    @JoinTable(
        name = "user_categories",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    private Set<Category> categories = new HashSet<>();

    // Для "понравившихся" категорий, те же связи
    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE }, fetch = FetchType.LAZY)
    @JoinTable(
            name = "user_categories", // используем ту же таблицу user_categories
            joinColumns = @JoinColumn(name = "user_id"),
            inverseJoinColumns = @JoinColumn(name = "category_id")
    )
    private Set<Category> favorites = new HashSet<>();

    // Геттеры и сеттеры для favorites
    public Set<Category> getFavorites() {
        return favorites;
    }

    public void setFavorites(Set<Category> favorites) {
        this.favorites = favorites;
    }

    // Методы для добавления/удаления категории из понравившихся
    public void addFavoriteCategory(Category category) {
        this.favorites.add(category);
    }

    public void removeFavoriteCategory(Category category) {
        this.favorites.remove(category);
    }

    public User() {
        // constructor
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public Set<Category> getCategories() {
        return categories;
    }

    public void setCategories(Set<Category> groups) {
        this.categories = groups;
    }

    public void addGroup(Category group) {
        categories.add(group);
        group.getUsers().add(this);
    }

    public void removeGroup(Category group) {
        categories.remove(group);
        group.getUsers().remove(this);
    }

    public void addPost(Response post) {
        responses.add(post);
        post.setUser(this);
    }

    public void removePost(Response post) {
        responses.remove(post);
        post.setUser(null);
    }
}