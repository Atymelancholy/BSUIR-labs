package com.example.bookblog.testservice;

import com.example.bookblog.cache.InMemoryCache;
import com.example.bookblog.entity.Book;
import com.example.bookblog.exception.BookAlreadyExistException;
import com.example.bookblog.repository.BookRepository;
import com.example.bookblog.service.BookService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class BookServiceTest {

    @Mock
    private BookRepository bookRepository;

    @Mock
    private InMemoryCache<Long, Book> bookCache;

    @InjectMocks
    private BookService bookService;

    private Book book1;
    private Book book2;

    @BeforeEach
    void setUp() {
        book1 = new Book();
        book1.setId(1L);
        book1.setTitle("Book One");
        book1.setAuthor("Author One");

        book2 = new Book();
        book2.setId(2L);
        book2.setTitle("Book Two");
        book2.setAuthor("Author Two");
    }

    @Test
    void testGetAllBooks() {
        when(bookRepository.findAll()).thenReturn(Arrays.asList(book1, book2));
        List<Book> books = bookService.getAllBooks();
        assertEquals(2, books.size());
        verify(bookRepository, times(1)).findAll();
    }

    @Test
    void testGetBookById_WhenExists() throws BookNotFoundException {
        when(bookRepository.findById(1L)).thenReturn(Optional.of(book1));
        Optional<Book> book = bookService.getBookById(1L);
        assertTrue(book.isPresent());
        assertEquals("Book One", book.get().getTitle());
        verify(bookRepository, times(1)).findById(1L);
    }

    @Test
    void testGetBookById_WhenNotExists() {
        when(bookRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(BookNotFoundException.class, () -> bookService.getBookById(1L));
        verify(bookRepository, times(1)).findById(1L);
    }

    @Test
    void testCreateBook_Success() throws BookAlreadyExistException {
        Book newBook = new Book();
        newBook.setTitle("New Book");
        newBook.setAuthor("New Author");

        when(bookRepository.existsByTitleAndAuthor(anyString(), anyString())).thenReturn(false);
        bookService.createBook(newBook);
        verify(bookRepository, times(1)).save(newBook);
    }

    @Test
    void testCreateBook_AlreadyExists() {
        when(bookRepository.existsByTitleAndAuthor(book1.getTitle(), book1.getAuthor())).thenReturn(true);
        assertThrows(BookAlreadyExistException.class, () -> bookService.createBook(book1));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testCreateBook_InvalidData() {
        Book invalidBook = new Book();
        assertThrows(ValidationException.class, () -> bookService.createBook(invalidBook));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testUpdateBook_Success() throws BookNotFoundException {
        when(bookRepository.findById(1L)).thenReturn(Optional.of(book1));
        book1.setTitle("Updated Title");
        bookService.updateBook(1L, book1);
        verify(bookRepository, times(1)).save(book1);
        verify(bookCache, times(1)).put(1L, book1);
    }

    @Test
    void testUpdateBook_NotFound() {
        when(bookRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(BookNotFoundException.class, () -> bookService.updateBook(1L, book1));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testDeleteBook_Success() throws BookNotFoundException {
        when(bookRepository.findById(1L)).thenReturn(Optional.of(book1));
        bookService.deleteBook(1L);
        verify(bookRepository, times(1)).delete(book1);
        verify(bookCache, times(1)).remove(1L);
    }

    @Test
    void testDeleteBook_NotFound() {
        when(bookRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(BookNotFoundException.class, () -> bookService.deleteBook(1L));
        verify(bookRepository, never()).delete(any());
    }

    @Test
    void testExistsByTitleAndAuthor_WhenNotExists() {
        when(bookRepository.existsByTitleAndAuthor("Unknown", "Author")).thenReturn(false);
        boolean exists = bookService.existsByTitleAndAuthor("Unknown", "Author");
        assertFalse(exists);
        verify(bookRepository, times(1)).existsByTitleAndAuthor("Unknown", "Author");
    }

    @Test
    void testSaveBooksBulk_Success() {
        List<Book> books = Arrays.asList(book1, book2);
        when(bookRepository.saveAll(books)).thenReturn(books);
        List<Book> savedBooks = bookService.saveBooksBulk(books);
        assertEquals(2, savedBooks.size());
        verify(bookRepository, times(1)).saveAll(books);
    }

    @Test
    void testCreateBook_WithId_ShouldThrowException() {
        Book bookWithId = new Book();
        bookWithId.setId(100L);
        bookWithId.setTitle("Title");
        bookWithId.setAuthor("Author");

        assertThrows(IllegalArgumentException.class, () -> bookService.createBook(bookWithId));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testCreateBook_WithEmptyTitle_ShouldThrowValidationException() {
        Book invalidBook = new Book();
        invalidBook.setTitle("");
        invalidBook.setAuthor("Author");

        assertThrows(ValidationException.class, () -> bookService.createBook(invalidBook));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testCreateBook_WithEmptyAuthor_ShouldThrowValidationException() {
        Book invalidBook = new Book();
        invalidBook.setTitle("Title");
        invalidBook.setAuthor("");

        assertThrows(ValidationException.class, () -> bookService.createBook(invalidBook));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testUpdateBook_WithEmptyTitle_ShouldThrowValidationException() throws BookNotFoundException {
        when(bookRepository.findById(1L)).thenReturn(Optional.of(book1));
        book1.setTitle("");

        assertThrows(ValidationException.class, () -> bookService.updateBook(1L, book1));
        verify(bookRepository, never()).save(any());
    }

    @Test
    void testUpdateBook_WithEmptyAuthor_ShouldThrowValidationException() throws BookNotFoundException {
        when(bookRepository.findById(1L)).thenReturn(Optional.of(book1));
        book1.setAuthor("");

        assertThrows(ValidationException.class, () -> bookService.updateBook(1L, book1));
        verify(bookRepository, never()).save(any());
    }
}
