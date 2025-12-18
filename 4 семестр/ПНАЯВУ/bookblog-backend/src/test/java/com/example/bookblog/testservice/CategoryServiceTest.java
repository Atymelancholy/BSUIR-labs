package com.example.bookblog.testservice;

import com.example.bookblog.cache.InMemoryCache;
import com.example.bookblog.dto.CategoryWithUsersDto;
import com.example.bookblog.entity.Category;
import com.example.bookblog.exception.CategoryAlreadyExistException;
import com.example.bookblog.exception.CategoryNotFoundException;
import com.example.bookblog.exception.ValidationException;
import com.example.bookblog.repository.CategoryRepository;
import com.example.bookblog.repository.UserRepository;
import com.example.bookblog.service.CategoryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CategoryServiceTest {

    @Mock
    private CategoryRepository categoryRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private InMemoryCache<Long, CategoryWithUsersDto> categoryCache;

    @Mock
    private InMemoryCache<String, List<CategoryWithUsersDto>> searchCache;

    @InjectMocks
    private CategoryService categoryService;

    private Category category1;
    private Category category2;

    @BeforeEach
    void setUp() {
        category1 = new Category();
        category1.setId(1L);
        category1.setName("Test Category");

        category2 = new Category();
        category2.setId(2L);
        category2.setName("Another Category");
    }

    @Test
    void testRegistration_Success() throws CategoryAlreadyExistException {
        when(categoryRepository.save(any(Category.class))).thenAnswer(invocation -> {
            Category savedCategory = invocation.getArgument(0);
            savedCategory.setId(1L);
            return savedCategory;
        });

        Category registeredCategory = categoryService.registration(category1);

        assertNotNull(registeredCategory.getId());
        verify(categoryRepository, times(1)).save(category1);
    }

    @Test
    void testRegistration_AlreadyExists() {
        when(categoryRepository.findByName(category1.getName())).thenReturn(category1);
        assertThrows(CategoryAlreadyExistException.class, () -> categoryService.registration(category1));
        verify(categoryRepository, never()).save(any());
    }

    @Test
    void testRegistration_InvalidData() {
        Category invalidCategory = new Category();
        assertThrows(ValidationException.class, () -> categoryService.registration(invalidCategory));
        verify(categoryRepository, never()).save(any());
    }

    @Test
    void testUpdateGroup_Success() throws CategoryNotFoundException {
        Category updatedCategory = new Category();
        updatedCategory.setName("Updated Name");

        when(categoryRepository.findById(1L)).thenReturn(Optional.of(category1));

        categoryService.updateGroup(1L, updatedCategory);

        assertEquals("Updated Name", category1.getName());
        verify(searchCache).clear();
    }
    @Test
    void testUpdateGroup_NotFound() {
        when(categoryRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(CategoryNotFoundException.class, () -> categoryService.updateGroup(1L, category1));
    }

    @Test
    void testDeleteGroup_NotFound() {
        when(categoryRepository.findById(1L)).thenReturn(Optional.empty());
        assertThrows(CategoryNotFoundException.class, () -> categoryService.deleteGroup(1L));
    }

    @Test
    void testRegistration_EmptyName() {
        Category emptyNameCategory = new Category();
        emptyNameCategory.setName("");

        assertThrows(ValidationException.class,
                () -> categoryService.registration(emptyNameCategory));
        verify(categoryRepository, never()).save(any());
    }

    @Test
    void testUpdateGroup_EmptyName() {
        Category updatedCategory = new Category();
        updatedCategory.setName("");

        when(categoryRepository.findById(1L)).thenReturn(Optional.of(category1));

        assertThrows(ValidationException.class,
                () -> categoryService.updateGroup(1L, updatedCategory));
        verify(categoryRepository, never()).save(any());
    }
}
