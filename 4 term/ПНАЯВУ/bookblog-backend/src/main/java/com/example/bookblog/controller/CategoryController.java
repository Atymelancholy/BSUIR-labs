package com.example.bookblog.controller;

import com.example.bookblog.dto.CategoryWithUsersDto;
import com.example.bookblog.entity.Category;
import com.example.bookblog.exception.CategoryAlreadyExistException;
import com.example.bookblog.exception.CategoryNotFoundException;
import com.example.bookblog.service.CategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/categories")
@Tag(name = "Category Controller", description = "API для управления категориями")
public class CategoryController {
    private final CategoryService groupService;

    @Autowired
    public CategoryController(CategoryService groupService) {
        this.groupService = groupService;
    }

    @Operation(summary = "Фильтрация категорий по количеству пользователей",
            description = "Возвращает категории, "
                    + "в которых число пользователей больше или равно указанному")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категории найдены"),
        @ApiResponse(responseCode = "400", description = "Неверный запрос")
    })
    @GetMapping("/filter-by-users")
    public List<CategoryWithUsersDto> getCategoriesByMinUsers(@RequestParam int minUsers) {
        return groupService.findCategoriesByMinUsers(minUsers);
    }

    @Operation(summary = "Фильтрация категорий (native query)",
            description = "Фильтрует категории по количеству "
                    + "пользователей с использованием native SQL")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категории найдены"),
        @ApiResponse(responseCode = "400", description = "Неверный запрос")
    })
    @GetMapping("/filter-by-users-native")
    public List<CategoryWithUsersDto> getCategoriesByMinUsersNative(@RequestParam int minUsers) {
        return groupService.findCategoriesByMinUsersNative(minUsers);
    }

    @Operation(summary = "Добавление категории", description = "Создает новую категорию")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категория добавлена"),
        @ApiResponse(responseCode = "400", description = "Категория уже существует"),
        @ApiResponse(responseCode = "500", description = "Ошибка сервера")
    })
    @PostMapping
    public ResponseEntity<?> registrationGroup(@Valid @RequestBody Category group,
                                               BindingResult result) {
        if (result.hasErrors()) {
            String errorMessages = result.getAllErrors()
                    .stream()
                    .map(error -> error.getDefaultMessage())
                    .collect(Collectors.joining(", "));
            return ResponseEntity.badRequest().body(errorMessages);
        }

        try {
            groupService.registration(group);
            return ResponseEntity.ok().body("Category added");
        } catch (CategoryAlreadyExistException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Error T_T");
        }
    }

    @Operation(summary = "Получение категории по ID",
            description = "Возвращает информацию о категории по ее ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категория найдена"),
        @ApiResponse(responseCode = "404", description = "Категория не найдена")
    })
    @GetMapping("/{id}")
    public ResponseEntity<CategoryWithUsersDto> getOneGroupPath(@PathVariable Long id) {
        try {
            CategoryWithUsersDto group = groupService.getOne(id);
            return ResponseEntity.ok(group);
        } catch (CategoryNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Удаление категории", description = "Удаляет категорию по ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категория успешно удалена"),
        @ApiResponse(responseCode = "404", description = "Категория не найдена")
    })
    @DeleteMapping("/{id}")
    public ResponseEntity<String> deleteGroup(@PathVariable Long id) {
        try {
            groupService.deleteGroup(id);
            return ResponseEntity.ok("Category deleted successfully");
        } catch (CategoryNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Обновление категории", description = "Обновляет данные категории по ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категория обновлена"),
        @ApiResponse(responseCode = "404", description = "Категория не найдена"),
        @ApiResponse(responseCode = "400", description = "Ошибка при обновлении категории")
    })
    @PutMapping("/{id}")
    public ResponseEntity<String> updateGroup(@PathVariable Long id,
                                              @RequestBody Category updatedGroup) {
        try {
            groupService.updateGroup(id, updatedGroup);
            return ResponseEntity.ok("Category updated successfully!");
        } catch (CategoryNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error...");
        }
    }

    @Operation(summary = "Категории пользователя",
            description = "Возвращает категории, которые выбрал пользователь")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категории получены"),
        @ApiResponse(responseCode = "404", description = "Пользователь не найден")
    })
    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Category>> getCategoriesByUserId(@PathVariable Long userId) {
        List<Category> categories = groupService.getCategoriesByUserId(userId);
        return ResponseEntity.ok(categories);
    }

    @Operation(summary = "Получить все категории")
    @GetMapping
    public ResponseEntity<List<Category>> getAllCategories() {
        List<Category> categories = groupService.getAll();
        return ResponseEntity.ok(categories);
    }




}
