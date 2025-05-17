package com.example.bookblog.dto;

import com.example.bookblog.entity.Category;

public class CategoryDto {
    private Long id;
    private String name;

    public static CategoryDto toModel(Category entity) {
        CategoryDto model = new CategoryDto();
        model.setId(entity.getId());
        model.setName(entity.getName());

        return model;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
