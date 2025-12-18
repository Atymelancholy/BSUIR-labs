package com.example.bookblog.testservice;

import com.example.bookblog.entity.Category;
import com.example.bookblog.entity.User;
import com.example.bookblog.exception.CategoryNotFoundException;
import com.example.bookblog.exception.UserAlreadyExistException;
import com.example.bookblog.exception.UserNotFoundException;
import com.example.bookblog.exception.ValidationException;
import com.example.bookblog.repository.CategoryRepository;
import com.example.bookblog.repository.UserRepository;
import com.example.bookblog.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private CategoryRepository categoryRepository;

    @InjectMocks
    private UserService userService;

    private User user;
    private Category category;

    @BeforeEach
    void setUp() {
        user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setPassword("password");

        category = new Category();
        category.setId(1L);
        category.setName("Test Category");
    }

    @Test
    void testRegistration_Success() throws Exception {
        when(userRepository.findByUsername(user.getUsername())).thenReturn(null);
        when(userRepository.save(user)).thenReturn(user);

        User registeredUser = userService.registration(user);

        assertNotNull(registeredUser);
        assertEquals("testuser", registeredUser.getUsername());
        verify(userRepository, times(1)).save(user);
    }

    @Test
    void testRegistration_UserAlreadyExists() {
        when(userRepository.findByUsername(user.getUsername())).thenReturn(user);
        assertThrows(UserAlreadyExistException.class, () -> userService.registration(user));
        verify(userRepository, never()).save(any());
    }

    @Test
    void testGetOne_UserExists () throws Exception {
        when(userRepository.findWithPostsAndGroupsById(user.getId())).thenReturn(Optional.of(user));
        assertNotNull(userService.getOne(user.getId()));
        verify(userRepository, times(1)).findWithPostsAndGroupsById(user.getId());
    }

    @Test
    void testGetOne_UserNotFound() {
        when(userRepository.findWithPostsAndGroupsById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> userService.getOne(user.getId()));
    }

    @Test
    void testAddUserToGroup_Success() throws Exception {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(userRepository.findWithPostsAndGroupsById(user.getId())).thenReturn(Optional.of(user)); // Добавлено
        when(categoryRepository.findById(category.getId())).thenReturn(Optional.of(category));

        userService.addUserToGroup(user.getId(), category.getId());

        verify(userRepository, times(1)).save(user);
    }


    @Test
    void testAddUserToGroup_UserNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> userService.addUserToGroup(user.getId(), category.getId()));
    }

    @Test
    void testAddUserToGroup_CategoryNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(categoryRepository.findById(category.getId())).thenReturn(Optional.empty());
        assertThrows(CategoryNotFoundException.class, () -> userService.addUserToGroup(user.getId(), category.getId()));
    }

    @Test
    void testDeleteUser_Success() throws Exception {
        when(userRepository.existsById(user.getId())).thenReturn(true);
        doNothing().when(userRepository).deleteById(user.getId());
        userService.delete(user.getId());
        verify(userRepository, times(1)).deleteById(user.getId());
    }

    @Test
    void testDeleteUser_UserNotFound() {
        when(userRepository.existsById(user.getId())).thenReturn(false);
        assertThrows(UserNotFoundException.class, () -> userService.delete(user.getId()));
    }

    @Test
    void testRegistration_EmptyUsername() {
        user.setUsername("");
        assertThrows(ValidationException.class, () -> userService.registration(user));
        verify(userRepository, never()).save(any());
    }

    @Test
    void testRegistration_EmptyPassword() {
        user.setPassword("");
        assertThrows(ValidationException.class, () -> userService.registration(user));
        verify(userRepository, never()).save(any());
    }

    @Test
    void testGetUserById_Success() throws Exception {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        User foundUser = userService.getUserById(user.getId());
        assertEquals(user, foundUser);
        verify(userRepository, times(1)).findById(user.getId());
    }

    @Test
    void testGetUserById_NotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> userService.getUserById(user.getId()));
    }

    @Test
    void testUpdateUser_Success() throws Exception {
        User updatedUser = new User();
        updatedUser.setUsername("updated");
        updatedUser.setPassword("newpassword");

        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(userRepository.findWithPostsAndGroupsById(user.getId())).thenReturn(Optional.of(user));

        userService.updateUser(user.getId(), updatedUser);

        assertEquals("updated", user.getUsername());
        assertEquals("newpassword", user.getPassword());
        verify(userRepository, times(1)).save(user);
    }

    @Test
    void testUpdateUser_UserNotFound() {
        User updatedUser = new User();
        updatedUser.setUsername("updated");
        updatedUser.setPassword("newpassword");

        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> userService.updateUser(user.getId(), updatedUser));
    }

    @Test
    void testUpdateUser_EmptyUsername() {
        User updatedUser = new User();
        updatedUser.setUsername("");
        updatedUser.setPassword("valid");

        assertThrows(ValidationException.class, () -> userService.updateUser(user.getId(), updatedUser));

        verify(userRepository, never()).findById(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void testUpdateUser_EmptyPassword() {
        User updatedUser = new User();
        updatedUser.setUsername("valid");
        updatedUser.setPassword("");

        assertThrows(ValidationException.class, () -> userService.updateUser(user.getId(), updatedUser));

        verify(userRepository, never()).findById(any());
        verify(userRepository, never()).save(any());
    }

    @Test
    void testRemoveUserFromGroup_Success() throws Exception {
        user.addGroup(category);
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(categoryRepository.findById(category.getId())).thenReturn(Optional.of(category));

        userService.removeUserFromGroup(user.getId(), category.getId());

        verify(userRepository, times(1)).save(user);
        assertFalse(user.getCategories().contains(category));
    }

    @Test
    void testRemoveUserFromGroup_UserNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class,
                () -> userService.removeUserFromGroup(user.getId(), category.getId()));
    }

    @Test
    void testRemoveUserFromGroup_CategoryNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(categoryRepository.findById(category.getId())).thenReturn(Optional.empty());
        assertThrows(CategoryNotFoundException.class,
                () -> userService.removeUserFromGroup(user.getId(), category.getId()));
    }

    @Test
    void testGetUserGroups_Success() throws Exception {
        user.addGroup(category);
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));

        Set<Category> groups = userService.getUserGroups(user.getId());

        assertEquals(1, groups.size());
        assertTrue(groups.contains(category));
        verify(userRepository, times(1)).findById(user.getId());
    }

    @Test
    void testGetUserGroups_UserNotFound() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> userService.getUserGroups(user.getId()));
    }
}
