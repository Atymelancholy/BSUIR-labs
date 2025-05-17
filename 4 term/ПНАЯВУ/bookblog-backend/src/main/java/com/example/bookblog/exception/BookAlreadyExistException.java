package com.example.bookblog.exception;

public class BookAlreadyExistException extends RuntimeException {

    // Constructor that takes a message
    public BookAlreadyExistException(String message) {
        super(message);
    }
}
