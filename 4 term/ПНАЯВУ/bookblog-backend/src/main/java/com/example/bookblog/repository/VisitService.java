package com.example.bookblog.repository;

import com.example.bookblog.dto.VisitStatsDto;

public interface VisitService {
    void recordVisit(String url);

    VisitStatsDto getVisitStats(String url);
}