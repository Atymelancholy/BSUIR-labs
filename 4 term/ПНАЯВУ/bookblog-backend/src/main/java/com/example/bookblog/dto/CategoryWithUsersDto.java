package com.example.bookblog.dto;

import com.example.bookblog.entity.Category;
import java.util.List;

public class CategoryWithUsersDto {
    private Long id;
    private String name;

    private List<UserDto> users;

    public static CategoryWithUsersDto toModel(Category entity) {
        CategoryWithUsersDto model = new CategoryWithUsersDto();
        model.setId(entity.getId());
        model.setName(entity.getName());

        model.setUsers(entity.getUsers().stream()
                .map(UserDto::toModel)
                .toList());
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

    public void setUsers(List<UserDto> users) {
        this.users = users;
    }
}
