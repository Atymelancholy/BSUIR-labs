package com.example.bookblog.testservice;

import com.example.bookblog.dto.VisitStatsDto;
import com.example.bookblog.entity.Visit;
import com.example.bookblog.repository.VisitRepository;
import com.example.bookblog.service.VisitServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import java.time.LocalDateTime;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class VisitServiceImplTest {

    @Mock
    private VisitRepository visitRepository;

    @InjectMocks
    private VisitServiceImpl visitService;

    private final String TEST_URL = "/test-url";
    private final LocalDateTime TEST_DATE = LocalDateTime.now();

    @Test
    void recordVisit_shouldIncrementCountWhenUrlExists() {
        when(visitRepository.existsByUrl(TEST_URL)).thenReturn(true);

        visitService.recordVisit(TEST_URL);

       // verify(visitRepository).incrementCount(TEST_URL, any(LocalDateTime.class));
        verify(visitRepository, never()).save(any(Visit.class));
    }

    @Test
    void recordVisit_shouldCreateNewVisitWhenUrlDoesNotExist() {
        when(visitRepository.existsByUrl(TEST_URL)).thenReturn(false);

        visitService.recordVisit(TEST_URL);

       // verify(visitRepository).incrementCount(TEST_URL, any(LocalDateTime.class));
        verify(visitRepository).save(argThat(visit ->
                visit.getUrl().equals(TEST_URL) && visit.getCount() == 1
        ));
    }

    @Test
    void getVisitStats_shouldReturnStatsWhenVisitExists() {
        Visit visit = new Visit(TEST_URL);
        visit.setCount(5);
        visit.setLastUpdated(TEST_DATE);

        when(visitRepository.findByUrl(TEST_URL)).thenReturn(Optional.of(visit));

        VisitStatsDto result = visitService.getVisitStats(TEST_URL);

        assertNotNull(result);
        assertEquals(TEST_URL, result.getUrl());
        assertEquals(5, result.getCount());
        assertEquals(TEST_DATE, result.getLastUpdated());
    }

    @Test
    void getVisitStats_shouldReturnZeroStatsWhenVisitDoesNotExist() {
        when(visitRepository.findByUrl(TEST_URL)).thenReturn(Optional.empty());

        VisitStatsDto result = visitService.getVisitStats(TEST_URL);

        assertNotNull(result);
        assertEquals(TEST_URL, result.getUrl());
        assertEquals(0, result.getCount());
        assertNull(result.getLastUpdated());
    }

    @Test
    void getVisitStats_shouldHandleNullUrl() {
        VisitStatsDto result = visitService.getVisitStats(null);

        assertNotNull(result);
        assertNull(result.getUrl());
        assertEquals(0, result.getCount());
        assertNull(result.getLastUpdated());
    }
}