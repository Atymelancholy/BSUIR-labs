package com.example.bookblog.exception;

public class CategoryAlreadyExistException extends Exception {
    public CategoryAlreadyExistException(String message) {
        super(message);
    }
}
