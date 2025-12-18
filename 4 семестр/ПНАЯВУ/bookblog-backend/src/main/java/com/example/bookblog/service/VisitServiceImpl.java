package com.example.bookblog.service;

import com.example.bookblog.dto.VisitStatsDto;
import com.example.bookblog.entity.Visit;
import com.example.bookblog.repository.VisitRepository;
import com.example.bookblog.repository.VisitService;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class VisitServiceImpl implements VisitService {
    private final VisitRepository visitRepo;
    private final Object lock = new Object();

    @Autowired
    public VisitServiceImpl(VisitRepository visitRepo) {
        this.visitRepo = visitRepo;
    }

    @Override
    @Transactional
    public void recordVisit(String url) {
        synchronized (lock) {
            visitRepo.incrementCount(url, LocalDateTime.now());
            if (!visitRepo.existsByUrl(url)) {
                Visit newVisit = new Visit(url);
                newVisit.setCount(1);
                visitRepo.save(newVisit);
            }
        }
    }

    @Override
    public VisitStatsDto getVisitStats(String url) {
        Optional<Visit> visit = visitRepo.findByUrl(url);
        return visit.map(v -> new VisitStatsDto(
                        v.getUrl(),
                        v.getCount(),
                        v.getLastUpdated()))
                .orElse(new VisitStatsDto(url, 0, null));
    }
}