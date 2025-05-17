package com.example.bookblog.service;

import com.example.bookblog.cache.InMemoryCache;
import com.example.bookblog.entity.Book;
import com.example.bookblog.entity.Category;
import com.example.bookblog.exception.BookAlreadyExistException;
import com.example.bookblog.exception.BookNotFoundException;
import com.example.bookblog.exception.ValidationException;
import com.example.bookblog.repository.BookRepository;
import java.util.List;
import java.util.Optional;

import com.example.bookblog.repository.CategoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class BookService {

    @Autowired
    private BookRepository bookRepository;

    @Autowired
    private InMemoryCache<Long, Book> bookCache;

    public List<Book> getAllBooks() {
        return bookRepository.findAll();
    }

    public Optional<Book> getBookById(Long id) throws BookNotFoundException {
        Optional<Book> book = bookRepository.findById(id);
        if (book.isEmpty()) {
            throw new BookNotFoundException("Book with this ID not found!");
        }
        return book;
    }

    public Book createBook(Book book) throws BookAlreadyExistException {
        if (bookRepository.existsByTitleAndAuthor(book.getTitle(), book.getAuthor())) {
            throw new BookAlreadyExistException("A book with "
                    + "this title and author already exists!");
        }

        if (book.getId() != null) {
            throw new IllegalArgumentException("The id should be null for new books");
        }

        if (book.getTitle() == null || book.getTitle().trim().isEmpty()) {
            throw new ValidationException("Title must not be empty");
        }

        if (book.getAuthor() == null || book.getAuthor().trim().isEmpty()) {
            throw new ValidationException("Author must not be empty");
        }

        bookRepository.save(book);
        return book;
    }

    public boolean existsByTitleAndAuthor(String title, String author) {
        return bookRepository.existsByTitleAndAuthor(title, author);
    }

    public List<Book> saveBooksBulk(List<Book> books) {
        return bookRepository.saveAll(books);
    }

    public void updateBook(Long id, Book updatedBook) throws BookNotFoundException {
        Book existingBook = bookRepository.findById(id).orElseThrow(() ->
                new BookNotFoundException("Book with this ID not found"));

        if (updatedBook.getTitle().isBlank() || updatedBook.getAuthor().isBlank()) {
            throw new ValidationException("Title and Author must not be empty");
        }

        existingBook.setTitle(updatedBook.getTitle());
        existingBook.setAuthor(updatedBook.getAuthor());
        bookRepository.save(existingBook);
        bookCache.put(id, existingBook);
    }

    public void deleteBook(Long id) throws BookNotFoundException {
        Book book = bookRepository.findById(id).orElseThrow(()
                -> new BookNotFoundException("Book with this ID not found"));
        bookRepository.delete(book);
        bookCache.remove(id);
    }

    public List<Book> getBooksByCategoryId(Long categoryId) {
        return bookRepository.findByCategories_Id(categoryId);
    }

    @Autowired
    private CategoryRepository categoryRepository;

    public void addCategoryToBook(Long bookId, Long categoryId) {
        Book book = bookRepository.findById(bookId).orElseThrow(() ->
                new BookNotFoundException("Book with this ID not found"));

        Category category = categoryRepository.findById(categoryId).orElseThrow(() ->
                new RuntimeException("Category with this ID not found"));

        book.addCategory(category);
        bookRepository.save(book);
    }

    public void removeCategoryFromBook(Long bookId, Long categoryId) {
        Book book = bookRepository.findById(bookId).orElseThrow(() ->
                new BookNotFoundException("Book with this ID not found"));

        Category category = categoryRepository.findById(categoryId).orElseThrow(() ->
                new RuntimeException("Category with this ID not found"));

        book.removeCategory(category);
        bookRepository.save(book);
    }
}
