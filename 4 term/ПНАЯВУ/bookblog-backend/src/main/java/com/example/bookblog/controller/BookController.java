package com.example.bookblog.controller;

import com.example.bookblog.entity.Book;
import com.example.bookblog.exception.BookAlreadyExistException;
import com.example.bookblog.service.BookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@CrossOrigin(origins = "http://localhost:3000")
@RestController
@RequestMapping("/api/books")
@Tag(name = "Book Controller", description = "API для управления книгами")
public class BookController {

    @Autowired
    private BookService bookService;

    @Operation(summary = "Получение всех книг", description = "Возвращает список всех книг")
    @GetMapping
    public List<Book> getAllBooks() {
        return bookService.getAllBooks();
    }

    @Operation(summary = "Получение книги по ID", description = "Возвращает книгу по ее ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Книга найдена"),
            @ApiResponse(responseCode = "404", description = "Книга с таким ID не найдена")
    })
    @GetMapping("/{id}")
    public ResponseEntity<Book> getBookById(@PathVariable Long id) {
        Optional<Book> book = bookService.getBookById(id);
        return book.map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.notFound().build());
    }

    @Operation(summary = "Добавление новой книги", description = "Создает новую книгу")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Книга успешно добавлена"),
            @ApiResponse(responseCode = "400", description = "Ошибка при добавлении книги")
    })
    @PostMapping
    public ResponseEntity<Long> createBook(@RequestBody Book book) {
        try {
            Book createdBook = bookService.createBook(book);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdBook.getId());
        } catch (BookAlreadyExistException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(null);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(null);
        }
    }

    @Operation(summary = "Обновление книги", description = "Обновляет информацию о книге по ее ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Книга успешно обновлена"),
            @ApiResponse(responseCode = "400", description = "Ошибка при обновлении книги")
    })
    @PutMapping("/{id}")
    public ResponseEntity<String> updateBook(@PathVariable Long id, @RequestBody Book updatedBook) {
        try {
            bookService.updateBook(id, updatedBook);
            return ResponseEntity.ok("Book updated successfully");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error updating book");
        }
    }

    @Operation(summary = "Удаление книги", description = "Удаляет книгу по ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Книга успешно удалена"),
            @ApiResponse(responseCode = "404", description = "Книга с таким ID не найдена")
    })
    @DeleteMapping("/{id}")
    public ResponseEntity<String> deleteBook(@PathVariable Long id) {
        try {
            bookService.deleteBook(id);
            return ResponseEntity.ok("Book deleted successfully");
        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Operation(summary = "Добавление списка книг", description = "Позволяет добавить несколько книг за один запрос")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Книги успешно добавлены"),
            @ApiResponse(responseCode = "400", description = "Некорректные данные запроса")
    })
    @PostMapping(value = "/bulk")
    public ResponseEntity<List<Book>> addBooksBulk(@RequestBody List<Book> books) {
        if (books == null || books.isEmpty()) {
            throw new IllegalArgumentException("Book list must not be empty");
        }

        List<Book> validBooks = new ArrayList<>();

        for (Book book : books) {
            if (book.getTitle() == null || book.getTitle().trim().isEmpty()) {
                throw new IllegalArgumentException("Title must not be empty");
            }
            if (book.getAuthor() == null || book.getAuthor().trim().isEmpty()) {
                throw new IllegalArgumentException("Author must not be empty");
            }
            if (!bookService.existsByTitleAndAuthor(book.getTitle(), book.getAuthor())) {
                book.setId(null);
                validBooks.add(book);
            }
        }

        if (validBooks.isEmpty()) {
            throw new IllegalArgumentException("No valid books to add");
        }

        List<Book> savedBooks = bookService.saveBooksBulk(validBooks);
        return new ResponseEntity<>(savedBooks, HttpStatus.CREATED);
    }

    @Operation(summary = "Получение книг по категории", description = "Возвращает список книг, относящихся к категории")
    @GetMapping("/category/{categoryId}")
    public ResponseEntity<List<Book>> getBooksByCategoryId(@PathVariable Long categoryId) {
        List<Book> books = bookService.getBooksByCategoryId(categoryId);
        return ResponseEntity.ok(books);
    }

    @Operation(summary = "Добавление категории к книге", description = "Добавляет категорию к книге по ID")
    @PostMapping("/{bookId}/category/{categoryId}")
    public ResponseEntity<String> addCategoryToBook(@PathVariable Long bookId, @PathVariable Long categoryId) {
        try {
            bookService.addCategoryToBook(bookId, categoryId);
            return ResponseEntity.ok("Category added to book successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Book or Category not found");
        }
    }

    @Operation(summary = "Удаление категории из книги", description = "Удаляет категорию из книги по ID")
    @DeleteMapping("/{bookId}/category/{categoryId}")
    public ResponseEntity<String> removeCategoryFromBook(@PathVariable Long bookId, @PathVariable Long categoryId) {
        try {
            bookService.removeCategoryFromBook(bookId, categoryId);
            return ResponseEntity.ok("Category removed from book successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Book or Category not found");
        }
    }
}
