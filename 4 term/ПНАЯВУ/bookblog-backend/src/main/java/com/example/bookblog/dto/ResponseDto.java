package com.example.bookblog.dto;

import com.example.bookblog.entity.Response;

public class ResponseDto {
    private Long id;
    private String content;

    public static ResponseDto toModel(Response entity) {
        ResponseDto response = new ResponseDto();
        response.setId(entity.getId());
        response.setContent(entity.getContent());
        return response;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }
}
