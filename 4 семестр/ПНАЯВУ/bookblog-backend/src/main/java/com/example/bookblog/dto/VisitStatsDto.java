package com.example.bookblog.dto;

import java.time.LocalDateTime;

public class VisitStatsDto {
    private String url;
    private Integer count;
    private LocalDateTime lastUpdated;

    public VisitStatsDto(String url, Integer count, LocalDateTime lastUpdated) {
        this.url = url;
        this.count = count;
        this.lastUpdated = lastUpdated;
    }

    public String getUrl() {
        return url;
    }

    public Integer getCount() {
        return count;
    }

    public LocalDateTime getLastUpdated() {
        return lastUpdated;
    }
}