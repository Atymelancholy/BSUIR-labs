package com.example.bookblog;

import com.example.bookblog.exception.GlobalExceptionHandler;
import com.example.bookblog.exception.ValidationException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class GlobalExceptionHandlerTest {

    @InjectMocks
    private GlobalExceptionHandler globalExceptionHandler;

    @Test
    void handleValidationException_ReturnsBadRequestWithMessage() {
        String errorMessage = "Что-то не так";
        ValidationException exception = new ValidationException(errorMessage);

        Map<String, String> response = globalExceptionHandler.handleValidationException(exception);

        assertNotNull(response);
        assertEquals(errorMessage, response.get("Error"));
    }

    @Test
    void handleGeneralException_ReturnsInternalServerErrorWithMessage() {
        String errorMessage = "Что-то пошло не так";
        Exception exception = new Exception(errorMessage);

        ResponseEntity<String> response = globalExceptionHandler.handleGeneralException(exception);

        assertNotNull(response);
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertEquals("Произошла ошибка: " + errorMessage, response.getBody());
    }

    @Test
    void handleGeneralException_WithNullMessage_ReturnsDefaultMessage() {
        Exception exception = new Exception();

        ResponseEntity<String> response = globalExceptionHandler.handleGeneralException(exception);

        assertNotNull(response);
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertTrue(response.getBody().startsWith("Произошла ошибка: "));
    }
}