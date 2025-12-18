package com.example.bookblog.dto;

import com.example.bookblog.entity.User;
import java.util.List;

public class UserWithResponsesAndCategoryDto {
    private Long id;
    private String username;
    private List<ResponseDto> responses;
    private List<CategoryDto> categories;

    public static UserWithResponsesAndCategoryDto toModel(User entity) {
        UserWithResponsesAndCategoryDto model = new UserWithResponsesAndCategoryDto();
        model.setId(entity.getId());
        model.setUsername(entity.getUsername());

        model.setResponses(entity.getResponses().stream()
                .map(ResponseDto::toModel)
                .toList());

        model.setCategories(entity.getCategories().stream()
                .map(CategoryDto::toModel)
                .toList());
        return model;
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

    public List<ResponseDto> getResponses() {
        return responses;
    }

    public void setResponses(List<ResponseDto> responses) {
        this.responses = responses;
    }

    public List<CategoryDto> getCategories() {
        return categories;
    }

    public void setCategories(List<CategoryDto> categories) {
        this.categories = categories;
    }
}
