package com.example.bookblog.controller;

import com.example.bookblog.dto.VisitStatsDto;
import com.example.bookblog.repository.VisitService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/visits")
public class VisitController {
    private final VisitService visitService;

    @Autowired
    public VisitController(VisitService visitService) {
        this.visitService = visitService;
    }

    @PostMapping("/track")
    public ResponseEntity<Void> trackVisit(@RequestParam String url) {
        visitService.recordVisit(url);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/stats")
    public ResponseEntity<VisitStatsDto> getVisitStats(@RequestParam String url) {
        return ResponseEntity.ok(visitService.getVisitStats(url));
    }
}