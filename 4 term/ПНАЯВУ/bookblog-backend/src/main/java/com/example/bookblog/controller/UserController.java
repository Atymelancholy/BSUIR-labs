package com.example.bookblog.controller;

import com.example.bookblog.dto.UserLoginDto;
import com.example.bookblog.dto.UserWithResponsesAndCategoryDto;
import com.example.bookblog.entity.Category;
import com.example.bookblog.entity.User;
import com.example.bookblog.exception.CategoryNotFoundException;
import com.example.bookblog.exception.UserAlreadyExistException;
import com.example.bookblog.exception.UserNotFoundException;
import com.example.bookblog.exception.ValidationException;
import com.example.bookblog.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.Map;
import java.util.Set;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
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
@RequestMapping("/api/users")
@Tag(name = "User Controller", description = "API для управления пользователями")
public class UserController {
    private final UserService userService;

    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }

    @Operation(summary = "Регистрация пользователя",
            description = "Регистрирует нового пользователя")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь успешно добавлен"),
        @ApiResponse(responseCode = "400", description = "Ошибка при добавлении пользователя")
    })
    @PostMapping
    public ResponseEntity<String> registrationUser(@RequestBody User user)
            throws UserAlreadyExistException {
        userService.registration(user);
        return ResponseEntity.ok("User add...");
    }

    @Operation(summary = "Получение информации о пользователе",
            description = "Возвращает информацию о пользователе по его ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь найден"),
        @ApiResponse(responseCode = "404", description = "Пользователь не найден")
    })
    @GetMapping("/{id}")
    public ResponseEntity<UserWithResponsesAndCategoryDto> getOneUserPath(@PathVariable Long id) {
        try {
            UserWithResponsesAndCategoryDto user = userService.getOne(id);
            return ResponseEntity.ok(user);
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Удаление пользователя", description = "Удаляет пользователя по его ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь успешно удален"),
        @ApiResponse(responseCode = "404", description = "Пользователь не найден")
    })
    @DeleteMapping("/{id}")
    public ResponseEntity<String> deleteUser(@PathVariable Long id) {
        try {
            userService.delete(id);
            return ResponseEntity.ok("User deleted successfully");
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error");
        }
    }

    @Operation(summary = "Добавление пользователя в категорию",
            description = "Добавляет пользователя в категорию")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь добавлен в категорию"),
        @ApiResponse(responseCode = "404",
                description = "Пользователь или категория не найдены")
    })
    @PostMapping("/{userId}/categories/{groupId}")
    public ResponseEntity<String> addUserToGroup(@PathVariable Long userId,
                                                 @PathVariable Long groupId) {
        try {
            userService.addUserToGroup(userId, groupId);
            return ResponseEntity.ok("User added to group!");
        } catch (UserNotFoundException | CategoryNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Удаление пользователя из категории",
            description = "Удаляет пользователя из категории")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь удален из категории"),
        @ApiResponse(responseCode = "404",
                description = "Пользователь или категория не найдены")
    })
    @DeleteMapping("/{userId}/categories/{groupId}")
    public ResponseEntity<String> removeUserFromGroup(@PathVariable Long userId,
                                                      @PathVariable Long groupId) {
        try {
            userService.removeUserFromGroup(userId, groupId);
            return ResponseEntity.ok("User removed from group!");
        } catch (UserNotFoundException | CategoryNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Получение категорий пользователя",
            description = "Возвращает все категории, в которых состоит пользователь")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Категории пользователя получены"),
        @ApiResponse(responseCode = "404", description = "Пользователь не найден")
    })
    @GetMapping("/{userId}/categories")
    public ResponseEntity<Set<Category>> getUserGroups(@PathVariable Long userId) {
        try {
            return ResponseEntity.ok(userService.getUserGroups(userId));
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Обновление информации о пользователе",
            description = "Обновляет информацию о пользователе по ID")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Пользователь успешно обновлен"),
        @ApiResponse(responseCode = "404", description = "Пользователь не найден"),
        @ApiResponse(responseCode = "400", description = "Ошибка при обновлении пользователя")
    })
    @PutMapping("/{id}")
    public ResponseEntity<String> updateUser(@PathVariable Long id,
                                             @RequestBody User updatedUser) {
        try {
            userService.updateUser(id, updatedUser);
            return ResponseEntity.ok("User updated successfully!");
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error updating user.");
        }
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        try {
            User created = userService.registration(user);
            return ResponseEntity.ok(created);
        } catch (UserAlreadyExistException | ValidationException e) {
            return ResponseEntity.badRequest().body(Map.of("message", e.getMessage()));
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> loginUser(@RequestBody UserLoginDto loginDto) {
        System.out.println("Метод loginUser вызван с username: " + loginDto.getUsername());

        try {
            User user = userService.authenticate(loginDto.getUsername(), loginDto.getPassword());
            return ResponseEntity.ok(user);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(e.getMessage());
        }
    }

    @PostMapping("/{userId}/favorites/{categoryId}")
    public ResponseEntity<String> addCategoryToFavorites(@PathVariable Long userId, @PathVariable Long categoryId) {
        try {
            userService.addCategoryToFavorites(userId, categoryId);
            return ResponseEntity.ok("Категория добавлена в понравившиеся");
        } catch (UserNotFoundException | CategoryNotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }

    @DeleteMapping("/{userId}/favorites/{categoryId}")
    public ResponseEntity<String> removeCategoryFromFavorites(@PathVariable Long userId, @PathVariable Long categoryId) {
        try {
            userService.removeCategoryFromFavorites(userId, categoryId);
            return ResponseEntity.ok("Категория удалена из понравившихся");
        } catch (UserNotFoundException | CategoryNotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }
}
