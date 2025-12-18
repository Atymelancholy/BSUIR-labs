package com.example.bookblog.testservice;

import com.example.bookblog.entity.Book;
import com.example.bookblog.entity.Response;
import com.example.bookblog.entity.User;
import com.example.bookblog.exception.PostNotFoundException;
import com.example.bookblog.exception.UserNotFoundException;
import com.example.bookblog.repository.BookRepository;
import com.example.bookblog.repository.ResponseRepository;
import com.example.bookblog.repository.UserRepository;
import com.example.bookblog.service.ResponseService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ResponseServiceTest {

    @Mock
    private ResponseRepository responseRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private BookRepository bookRepository;

    @InjectMocks
    private ResponseService responseService;

    private User user;
    private Book book;
    private Response response;

    @BeforeEach
    void setUp() {
        user = new User();
        user.setId(1L);
        user.setUsername("testuser");

        book = new Book();
        book.setId(1L);
        book.setTitle("Test Book");

        response = new Response("Test response", user, book);
        response.setId(1L);
    }

    @Test
    void testCreateResponse_Success() throws Exception {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(bookRepository.findById(book.getId())).thenReturn(Optional.of(book));
        when(responseRepository.save(any(Response.class))).thenReturn(response);

        Response createdResponse = responseService.createResponse(user.getId(), book.getId(), "Test response");

        assertNotNull(createdResponse);
        assertEquals("Test response", createdResponse.getContent());
        verify(responseRepository, times(1)).save(any(Response.class));
    }

    @Test
    void testCreateResponse_UserNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> responseService.createResponse(user.getId(), book.getId(), "Test response"));
    }

    @Test
    void testGetUserResponses_Success() throws Exception {
        when(responseRepository.findByUserId(user.getId())).thenReturn(List.of(response));
        List<Response> responses = responseService.getUserResponses(user.getId());
        assertFalse(responses.isEmpty());
    }

    @Test
    void testGetBookResponses_Success() throws Exception {
        when(responseRepository.findByBookId(book.getId())).thenReturn(List.of(response));
        List<Response> responses = responseService.getBookResponses(book.getId());
        assertFalse(responses.isEmpty());
    }

    @Test
    void testDeleteResponse_NotFound() {
        when(responseRepository.findById(response.getId())).thenReturn(Optional.empty());
        assertThrows(PostNotFoundException.class, () -> responseService.deleteResponse(response.getId()));
    }

    @Test
    void testUpdateResponse_Success() throws Exception {
        when(responseRepository.findById(response.getId())).thenReturn(Optional.of(response));
        when(responseRepository.save(any(Response.class))).thenReturn(response);

        responseService.updateResponse(response.getId(), "Updated response");

        assertEquals("Updated response", response.getContent());
        verify(responseRepository, times(1)).save(response);
    }

    @Test
    void testUpdateResponse_NotFound() {
        when(responseRepository.findById(response.getId())).thenReturn(Optional.empty());
        assertThrows(PostNotFoundException.class, () -> responseService.updateResponse(response.getId(), "Updated response"));
    }

    @Test
    void testGetBookResponses_EmptyList() {
        when(responseRepository.findByBookId(book.getId())).thenReturn(Collections.emptyList());
        assertThrows(PostNotFoundException.class, () ->
                responseService.getBookResponses(book.getId()));
    }
}
