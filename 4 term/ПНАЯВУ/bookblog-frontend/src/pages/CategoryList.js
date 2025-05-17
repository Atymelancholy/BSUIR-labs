import React, { useEffect, useState, useContext } from 'react';
import {
    Box, Typography, List, ListItem, ListItemText, Divider,
    Button, TextField, Dialog, DialogActions, DialogContent, DialogTitle
} from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';
import bannerImage from '../assets/book.png';
import Header from '../components/Header';
import { AuthContext } from '../context/AuthContext';

const AllCategories = () => {
    const [categories, setCategories] = useState([]);
    const [newCategoryName, setNewCategoryName] = useState('');
    const [editingCategory, setEditingCategory] = useState(null);
    const [openCreateDialog, setOpenCreateDialog] = useState(false);
    const [openEditDialog, setOpenEditDialog] = useState(false);
    const [openBooksDialog, setOpenBooksDialog] = useState(false);
    const [selectedCategoryBooks, setSelectedCategoryBooks] = useState([]);
    const [selectedCategoryName, setSelectedCategoryName] = useState('');
    const [favoriteCategories, setFavoriteCategories] = useState([]);

    const { user } = useContext(AuthContext);

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/api/categories`)
            .then((res) => setCategories(res.data))
            .catch((err) => console.error('Ошибка при загрузке категорий:', err));

        if (user?.id) {
            axios.get(`${process.env.REACT_APP_API_URL}/api/categories/user/${user.id}`)
                .then(res => setFavoriteCategories(res.data.map(cat => cat.id)))
                .catch(err => console.error("Ошибка при загрузке избранных категорий", err));
        }
    }, [user]);

    const handleCreateCategory = () => {
        axios.post(`${process.env.REACT_APP_API_URL}/api/categories`, { name: newCategoryName })
            .then(() => {
                setCategories([...categories, { name: newCategoryName }]);
                setNewCategoryName('');
                setOpenCreateDialog(false);
            })
            .catch((err) => console.error('Ошибка при добавлении категории:', err));
    };

    const handleEditCategory = () => {
        if (editingCategory) {
            axios.put(`${process.env.REACT_APP_API_URL}/api/categories/${editingCategory.id}`, { name: editingCategory.name })
                .then(() => {
                    setCategories(categories.map(cat => (cat.id === editingCategory.id ? editingCategory : cat)));
                    setOpenEditDialog(false);
                })
                .catch((err) => console.error('Ошибка при обновлении категории:', err));
        }
    };

    const handleDeleteCategory = (id) => {
        axios.delete(`${process.env.REACT_APP_API_URL}/api/categories/${id}`)
            .then(() => {
                setCategories(categories.filter(cat => cat.id !== id));
            })
            .catch((err) => console.error('Ошибка при удалении категории:', err));
    };

    const handleCategoryClick = (categoryId, categoryName) => {
        axios.get(`${process.env.REACT_APP_API_URL}/api/books/category/${categoryId}`)
            .then((res) => {
                setSelectedCategoryBooks(res.data);
                setSelectedCategoryName(categoryName);
                setOpenBooksDialog(true);
            })
            .catch((err) => console.error('Ошибка при загрузке книг по категории:', err));
    };

    const toggleFavorite = async (categoryId) => {
        const isFavorite = favoriteCategories.includes(categoryId);
        const url = `${process.env.REACT_APP_API_URL}/api/users/${user.id}/favorites/${categoryId}`;
        const request = isFavorite ? axios.delete : axios.post;

        try {
            await request(url);
            // Обновляем локальное состояние после успешного запроса:
            const updatedFavorites = isFavorite
                ? favoriteCategories.filter(id => id !== categoryId)
                : [...favoriteCategories, categoryId];
            setFavoriteCategories(updatedFavorites); // Здесь обновляем состояние
        } catch (error) {
            console.error("Ошибка при обновлении избранного:", error);
        }
    };



    return (
        <>
            <Header />
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', md: 'row' },
                    height: '100vh',
                    padding: 2,
                    boxSizing: 'border-box',
                    backgroundColor: '#f4f4f4',
                    gap: 2,
                }}
            >
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.7 }}
                    style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        padding: '2rem',
                        borderRadius: '12px',
                    }}
                >
                    <Typography
                        variant="h4"
                        gutterBottom
                        sx={{
                            fontFamily: '"Playfair Display", serif',
                            textAlign: 'center',
                            marginBottom: 3,
                            fontWeight: 'bold',
                        }}
                    >
                        Список всех категорий
                    </Typography>
                    <Divider />
                    <List>
                        {categories.map((cat) => (
                            <ListItem key={cat.id}>
                                <ListItemText
                                    primary={
                                        <Button
                                            onClick={() => handleCategoryClick(cat.id, cat.name)}
                                            sx={{ textTransform: 'none', color: 'black', fontWeight: 'bold' }}
                                        >
                                            {cat.name}
                                        </Button>
                                    }
                                />
                                <Button onClick={() => toggleFavorite(cat.id)}>
                                    {favoriteCategories.includes(cat.id) ? (
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="gold">
                                            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                        </svg>
                                    ) : (
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="gray">
                                            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                        </svg>
                                    )}
                                </Button>

                                <Button
                                    onClick={() => {
                                        setEditingCategory(cat);
                                        setOpenEditDialog(true);
                                    }}
                                    sx={{ color: 'black' }}
                                >
                                    Редактировать
                                </Button>
                                <Button
                                    onClick={() => handleDeleteCategory(cat.id)}
                                    sx={{ color: 'black' }}
                                >
                                    Удалить
                                </Button>
                            </ListItem>
                        ))}
                    </List>
                    <Button
                        onClick={() => setOpenCreateDialog(true)}
                        sx={{ color: 'black' }}
                    >
                        Добавить новую категорию
                    </Button>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.7, delay: 0.2 }}
                    style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Box
                        sx={{
                            width: '90%',
                            height: '80%',
                            backgroundImage: `url(${bannerImage})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            borderRadius: '12px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                        }}
                    />
                </motion.div>
            </Box>

            {/* Диалоги */}
            <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)}>
                <DialogTitle>Добавить новую категорию</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Category Name"
                        fullWidth
                        variant="outlined"
                        value={newCategoryName}
                        onChange={(e) => setNewCategoryName(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenCreateDialog(false)} sx={{ color: 'black' }}>
                        Отмена
                    </Button>
                    <Button onClick={handleCreateCategory} sx={{ color: 'black' }}>
                        Добавить
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)}>
                <DialogTitle>Редактировать категорию</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Category Name"
                        fullWidth
                        variant="outlined"
                        value={editingCategory?.name || ''}
                        onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenEditDialog(false)} sx={{ color: 'black' }}>
                        Назад
                    </Button>
                    <Button onClick={handleEditCategory} sx={{ color: 'black' }}>
                        Сохранить
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={openBooksDialog} onClose={() => setOpenBooksDialog(false)}>
                <DialogTitle>Книги в категории: {selectedCategoryName}</DialogTitle>
                <DialogContent>
                    <List>
                        {selectedCategoryBooks.map((book) => (
                            <ListItem key={book.id}>
                                <ListItemText
                                    primary={book.title}
                                    secondary={`Автор: ${book.author}`}
                                />
                            </ListItem>
                        ))}
                    </List>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenBooksDialog(false)} sx={{ color: 'black' }}>
                        Закрыть
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};

export default AllCategories;
