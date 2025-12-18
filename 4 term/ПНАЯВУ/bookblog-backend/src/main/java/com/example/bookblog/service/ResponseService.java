package com.example.bookblog.service;

import com.example.bookblog.entity.Book;
import com.example.bookblog.entity.Response;
import com.example.bookblog.entity.User;
import com.example.bookblog.exception.BookNotFoundException;
import com.example.bookblog.exception.PostNotFoundException;
import com.example.bookblog.exception.UserNotFoundException;
import com.example.bookblog.exception.ValidationException;
import com.example.bookblog.repository.BookRepository;
import com.example.bookblog.repository.ResponseRepository;
import com.example.bookblog.repository.UserRepository;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

@Service
public class ResponseService {
    private final ResponseRepository responseRepository;
    private final UserRepository userRepository;
    private final BookRepository bookRepository;
    private final Map<Long, List<Response>> responseCache = new ConcurrentHashMap<>();

    public ResponseService(ResponseRepository responseRepository,
                           UserRepository userRepository, BookRepository bookRepository) {
        this.responseRepository = responseRepository;
        this.userRepository = userRepository;
        this.bookRepository = bookRepository;
    }

    public Response createResponse(Long userId, Long bookId, String content)
            throws UserNotFoundException, BookNotFoundException {
        if (content == null || content.trim().isEmpty()) {
            throw new ValidationException("Response content must not be empty");
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("User not found"));

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new BookNotFoundException("Book not found"));

        Response response = new Response(content, user, book);
        Response savedResponse = responseRepository.save(response);
        responseCache.remove(userId);
        return savedResponse;
    }

    public List<Response> getUserResponses(Long userId) throws PostNotFoundException {
        List<Response> responses = responseRepository.findByUserId(userId);
        if (responses.isEmpty()) {
            throw new PostNotFoundException("No responses found for user with id: " + userId);
        }

        responseCache.put(userId, responses);
        return responses;
    }

    public List<Response> getBookResponses(Long bookId) throws PostNotFoundException {
        List<Response> responses = responseRepository.findByBookId(bookId);
        if (responses.isEmpty()) {
            throw new PostNotFoundException("No responses found for book with id: " + bookId);
        }
        return responses;
    }

    public void deleteResponse(Long responseId) throws PostNotFoundException {
        Response response = responseRepository.findById(responseId)
                .orElseThrow(()
                        -> new PostNotFoundException("Response with id "
                        + responseId + " not found."));

        responseRepository.deleteById(responseId);
        responseCache.remove(response.getUser().getId());
        getUserResponses(response.getUser().getId());
        if (!responseRepository.findByUserId(response.getUser().getId()).isEmpty()) {
            getUserResponses(response.getUser().getId());
        }

    }

    public void updateResponse(Long responseId, String content) throws PostNotFoundException {
        if (content == null || content.trim().isEmpty()) {
            throw new ValidationException("Response content must not be empty");
        }

        Response response = responseRepository.findById(responseId)
                .orElseThrow(()
                        -> new PostNotFoundException("Response with this id does not exist!!!"));
        response.setContent(content);
        responseRepository.save(response);
        responseCache.clear();
    }
}