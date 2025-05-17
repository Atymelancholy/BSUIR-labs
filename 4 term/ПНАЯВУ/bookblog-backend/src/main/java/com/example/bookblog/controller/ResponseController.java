package com.example.bookblog.controller;

import com.example.bookblog.dto.ResponseDto;
import com.example.bookblog.entity.Response;
import com.example.bookblog.exception.BookNotFoundException;
import com.example.bookblog.exception.PostNotFoundException;
import com.example.bookblog.exception.UserNotFoundException;
import com.example.bookblog.service.ResponseService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/responses")
@Tag(name = "Response Controller", description = "API для управления отзывами")
public class ResponseController {
    private final ResponseService responseService;

    public ResponseController(ResponseService responseService) {
        this.responseService = responseService;
    }

    @Operation(summary = "Добавление отзыва для книги пользователем",
            description = "Создает новый отзыв для книги пользователем")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Отзыв успешно добавлен"),
        @ApiResponse(responseCode = "404", description = "Пользователь или книга не найдены"),
        @ApiResponse(responseCode = "400", description = "Ошибка при добавлении отзыва")
    })
    @PostMapping("/user/{userId}/book/{bookId}")
    public ResponseEntity<String> createResponse(@PathVariable Long userId,
                                                 @PathVariable Long bookId,
                                                 @RequestBody ResponseDto responseDto) {
        try {
            responseService.createResponse(userId, bookId, responseDto.getContent());
            return ResponseEntity.ok("Review successfully added");
        } catch (UserNotFoundException | BookNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error...");
        }
    }

    @Operation(summary = "Получение отзывов пользователя",
            description = "Возвращает все отзывы, оставленные пользователем")
    @ApiResponse(responseCode = "200", description = "Отзывы пользователя получены")
    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Response>> getUserResponses(@PathVariable Long userId) {
        try {
            return ResponseEntity.ok(responseService.getUserResponses(userId));
        } catch (PostNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Получение отзывов книги",
            description = "Возвращает все отзывы, оставленные на книгу")
    @ApiResponse(responseCode = "200", description = "Отзывы книги получены")
    @GetMapping("/book/{bookId}")
    public ResponseEntity<List<Response>> getBookResponses(@PathVariable Long bookId) {
        try {
            return ResponseEntity.ok(responseService.getBookResponses(bookId));
        } catch (PostNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Удаление отзыва", description = "Удаляет отзыв по его ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Отзыв успешно удален"),
        @ApiResponse(responseCode = "404", description = "Отзыв не найден")
    })
    @DeleteMapping("/{responseId}")
    public ResponseEntity<String> deleteResponse(@PathVariable Long responseId) {
        try {
            responseService.deleteResponse(responseId);
            return ResponseEntity.ok("Review deleted successfully");
        } catch (PostNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Обновление отзыва", description = "Обновляет контент отзыва по ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Отзыв успешно обновлен"),
        @ApiResponse(responseCode = "404", description = "Отзыв не найден"),
        @ApiResponse(responseCode = "400", description = "Ошибка при обновлении отзыва")
    })
    @PutMapping("/{responseId}")
    public ResponseEntity<String> updateResponse(@PathVariable Long responseId,
                                                 @RequestBody ResponseDto responseDto) {
        try {
            responseService.updateResponse(responseId, responseDto.getContent());
            return ResponseEntity.ok("Review updated successfully");
        } catch (PostNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error...");
        }
    }
}
