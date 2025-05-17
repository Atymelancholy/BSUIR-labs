import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Snackbar,
    Alert
} from '@mui/material';
import axios from 'axios';
import Header from "../components/Header";
import { MenuItem, Select, InputLabel, FormControl } from '@mui/material';

const BooksPage = () => {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [addDialogOpen, setAddDialogOpen] = useState(false);
    const [selectedBook, setSelectedBook] = useState(null);
    const [editData, setEditData] = useState({ title: '', author: '' });
    const [newBookData, setNewBookData] = useState({ title: '', author: '' });
    const [reviews, setReviews] = useState([]);
    const [newReview, setNewReview] = useState('');
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [openSnackbar, setOpenSnackbar] = useState(false);
    const [userId, setUserId] = useState(null);
    const [editingReviewId, setEditingReviewId] = useState(null);
    const [editedReviewText, setEditedReviewText] = useState('');
    const [editingReviewOpen, setEditingReviewOpen] = useState(false);
    const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
    const [reviewBook, setReviewBook] = useState(null);
    const [selectedCategoryId, setSelectedCategoryId] = useState('');
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/api/categories`)
            .then((res) => setCategories(res.data))
            .catch((err) => console.error('Ошибка при загрузке жанров:', err));
    }, []);


    useEffect(() => {
        const storedUser = localStorage.getItem("user");
        if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            setUserId(parsedUser.id);
        }
    }, []);

    useEffect(() => {
        console.log("API URL:", process.env.REACT_APP_API_URL);
        axios.get(`${process.env.REACT_APP_API_URL}/api/books`)


            .then((res) => {
                setBooks(res.data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Ошибка при загрузке книг:", err);
                setLoading(false);
            });
    }, []);

    const handleCardClick = (book) => {
        setSelectedBook(book);
        setEditData({ title: book.title, author: book.author });
        setDialogOpen(true);
    };

    const handleOpenReviewDialog = (book) => {
        setReviewBook(book);
        setReviewDialogOpen(true);
        axios.get(`${process.env.REACT_APP_API_URL}/api/responses/book/${book.id}`)
            .then((res) => setReviews(res.data))
            .catch((err) => {
                console.error("Ошибка при загрузке отзывов:", err);
                setReviews([]);
            });
    };

    const handleCloseReviewDialog = () => {
        setReviewDialogOpen(false);
        setReviewBook(null);
        setReviews([]);
        setNewReview('');
    };

    const handleCloseDialog = () => {
        setDialogOpen(false);
        setSelectedBook(null);
        setEditData({ title: '', author: '' });
    };

    const handleCloseAddDialog = () => {
        setAddDialogOpen(false);
        setNewBookData({ title: '', author: '' });
        setSelectedCategoryId('');

    };

    const handleSave = () => {
        if (!selectedBook) return;

        const updatedBook = {
            ...selectedBook,
            title: editData.title,
            author: editData.author
        };

        axios.put(`${process.env.REACT_APP_API_URL}/api/books/${selectedBook.id}`, updatedBook)
            .then(() => {
                setBooks((prev) =>
                    prev.map((b) => (b.id === selectedBook.id ? updatedBook : b))
                );
                handleCloseDialog();
                setSnackbarMessage('Книга успешно обновлена');
                setOpenSnackbar(true);
            })
            .catch((err) => {
                console.error("Ошибка при обновлении книги:", err);
            });
    };

    const handleDelete = () => {
        if (!selectedBook) return;

        axios.delete(`${process.env.REACT_APP_API_URL}/api/books/${selectedBook.id}`)
            .then(() => {
                setBooks((prev) => prev.filter((b) => b.id !== selectedBook.id));
                handleCloseDialog();
                setSnackbarMessage('Книга успешно удалена');
                setOpenSnackbar(true);
            })
            .catch((err) => {
                console.error("Ошибка при удалении книги:", err);
            });
    };

    const handleAddBook = () => {
        const newBook = {
            title: newBookData.title,
            author: newBookData.author,
            categoryId: selectedCategoryId
        };

        // Логируем книгу и жанр перед отправкой
        console.log('Перед отправкой на сервер:', newBook);
        console.log('Жанр перед отправкой:', selectedCategoryId);

        axios.post(`${process.env.REACT_APP_API_URL}/api/books`, newBook)
            .then((res) => {
                console.log('Ответ от сервера при создании книги:', res);

                const bookId = res.data;
                console.log('ID книги после создания:', bookId);

                if (!bookId || !selectedCategoryId) {
                    console.warn('Книга создана, но жанр не выбран');
                    setBooks((prev) => [...prev]);
                    handleCloseAddDialog();
                    setSnackbarMessage('Книга добавлена, но жанр не выбран');
                    setOpenSnackbar(true);
                    return;
                }

                axios.post(`${process.env.REACT_APP_API_URL}/api/books/${bookId}/category/${selectedCategoryId}`)
                    .then(() => {
                        setBooks((prev) => [{ id: bookId, title: newBookData.title, author: newBookData.author }, ...prev]); // Добавляем книгу с ID и данными
                        handleCloseAddDialog();
                        setSnackbarMessage('Книга и жанр успешно добавлены');
                        setOpenSnackbar(true);
                    })
                    .catch((err) => {
                        console.error('Ошибка при привязке жанра:', err);
                        setBooks((prev) => [{ id: bookId, title: newBookData.title, author: newBookData.author }, ...prev]); // Книга добавлена, но без привязки жанра
                        handleCloseAddDialog();
                        setSnackbarMessage('Книга добавлена, но жанр не удалось привязать');
                        setOpenSnackbar(true);
                    });
            })
            .catch((err) => {
                console.error("Ошибка при добавлении книги:", err);
                setSnackbarMessage('Ошибка при добавлении книги');
                setOpenSnackbar(true);
            });
    };




    const handleAddReview = () => {
        if (!reviewBook || !newReview.trim()) {
            setSnackbarMessage('Отзыв не может быть пустым');
            setOpenSnackbar(true);
            return;
        }

        if (!userId) {
            setSnackbarMessage('Пользователь не авторизован');
            setOpenSnackbar(true);
            return;
        }

        axios.post(`${process.env.REACT_APP_API_URL}/responses/user/${userId}/book/${reviewBook.id}`, {
            content: newReview
        })
            .then(() => {
                setReviews((prev) => [...prev, { content: newReview }]);
                setNewReview('');
                setSnackbarMessage('Отзыв успешно добавлен');
                setOpenSnackbar(true);
            })
            .catch((error) => {
                console.error('Ошибка при добавлении отзыва:', error);
                setSnackbarMessage('Ошибка при добавлении отзыва');
                setOpenSnackbar(true);
            });
    };

    const handleEditReview = (reviewId) => {
        const reviewToEdit = reviews.find(review => review.id === reviewId);
        setEditingReviewId(reviewId);
        setEditedReviewText(reviewToEdit.content);
        setEditingReviewOpen(true);
    };

    const handleSaveEditedReview = () => {
        if (!editedReviewText.trim()) {
            setSnackbarMessage('Отзыв не может быть пустым');
            setOpenSnackbar(true);
            return;
        }

        axios.put(`${process.env.REACT_APP_API_URL}/api/responses/${editingReviewId}`, { content: editedReviewText })
            .then(() => {
                setReviews((prev) => prev.map((review) =>
                    review.id === editingReviewId ? { ...review, content: editedReviewText } : review
                ));
                setSnackbarMessage('Отзыв успешно обновлен');
                setOpenSnackbar(true);
                setEditingReviewId(null);
                setEditedReviewText('');
                setEditingReviewOpen(false);
            })
            .catch((err) => {
                console.error('Ошибка при обновлении отзыва:', err);
                setSnackbarMessage('Ошибка при обновлении отзыва');
                setOpenSnackbar(true);
            });
    };

    const handleDeleteReview = (reviewId) => {
        axios.delete(`${process.env.REACT_APP_API_URL}/api/responses/${reviewId}`)
            .then(() => {
                setReviews((prev) => prev.filter((review) => review.id !== reviewId));
                setSnackbarMessage('Отзыв успешно удален');
                setOpenSnackbar(true);
            })
            .catch((err) => {
                console.error('Ошибка при удалении отзыва:', err);
                setSnackbarMessage('Ошибка при удалении отзыва');
                setOpenSnackbar(true);
            });
    };

    if (loading) return <CircularProgress sx={{ margin: '2rem auto', display: 'block' }} />;

    return (
        <>
            {/* 🔽 Вставка Header */}
            <Header />
        <Box sx={{ padding: '2rem' }}>
            <Typography variant="h4" gutterBottom>Список книг</Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                <Card
                    sx={{
                        width: '310px',
                        height: '200px',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        cursor: 'pointer',
                        border: '2px dashed grey',
                        boxSizing: 'border-box',
                        '&:hover': { backgroundColor: '#dbc986' },
                    }}
                    onClick={() => setAddDialogOpen(true)}
                >
                    <Typography variant="h5">+</Typography>
                </Card>

                {books.map((book) => (
                    <Card
                        key={book.id}
                        sx={{
                            width: '310px',
                            height: '200px',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            cursor: 'pointer',
                            boxSizing: 'border-box',
                            padding: 1,
                            '&:hover': { backgroundColor: '#dbc986' },
                        }}
                        onClick={() => handleCardClick(book)}
                    >
                        <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                            <Typography variant="h6" noWrap>{book.title}</Typography>
                            <Typography variant="body2" color="text.secondary" noWrap>{book.author}</Typography>
                        </CardContent>

                        <Box
                            sx={{
                                border: '1px solid #71a372',
                                borderRadius: '4px',
                                padding: '4px 8px',
                                mb: 1,
                            }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <Button
                                onClick={() => handleOpenReviewDialog(book)}
                                size="small"
                                sx={{ color: '#71a372', padding: 0, minWidth: 'auto' }}
                            >
                                Отзывы
                            </Button>
                        </Box>
                    </Card>
                ))}
            </Box>

            <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>Редактирование книги</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 400 }}>
                    <TextField
                        label="Название"
                        value={editData.title}
                        onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                        fullWidth
                        variant="outlined"
                        margin="normal"
                    />
                    <TextField
                        label="Автор"
                        value={editData.author}
                        onChange={(e) => setEditData({ ...editData, author: e.target.value })}
                        fullWidth
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleSave} variant="contained">Сохранить</Button>
                    <Button onClick={handleDelete} color="error">Удалить</Button>
                    <Button onClick={handleCloseDialog}>Отмена</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={addDialogOpen} onClose={handleCloseAddDialog} maxWidth="md" fullWidth>
                <DialogTitle>Добавить книгу</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 400 }}>
                    <TextField
                        label="Название"
                        value={newBookData.title}
                        onChange={(e) => setNewBookData({ ...newBookData, title: e.target.value })}
                        fullWidth
                        variant="outlined"
                        margin="normal"
                    />
                    <TextField
                        label="Автор"
                        value={newBookData.author}
                        onChange={(e) => setNewBookData({ ...newBookData, author: e.target.value })}
                        fullWidth
                    />
                    <FormControl fullWidth margin="normal">
                        <InputLabel id="category-label">Жанр</InputLabel>
                        <Select
                            labelId="category-label"
                            value={selectedCategoryId}
                            onChange={(e) => setSelectedCategoryId(e.target.value)}
                            label="Жанр"
                        >
                            {categories.map((cat) => (
                                <MenuItem key={cat.id} value={cat.id}>
                                    {cat.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                </DialogContent>
                <DialogActions>
                    <Button onClick={handleAddBook} variant="contained">Добавить</Button>
                    <Button onClick={handleCloseAddDialog}>Отмена</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={reviewDialogOpen} onClose={handleCloseReviewDialog} maxWidth="md" fullWidth>
                <DialogTitle>Отзывы о книге: {reviewBook?.title}</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {reviews.length > 0 ? (
                        reviews.map((review) => (
                            <Box key={review.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" sx={{ mb: 1 }}>• {review.content}</Typography>
                                <Box>
                                    <Button onClick={() => handleEditReview(review.id)} size="small">Редактировать</Button>
                                    <Button onClick={() => handleDeleteReview(review.id)} size="small" color="error">Удалить</Button>
                                </Box>
                            </Box>
                        ))
                    ) : (
                        <Typography variant="body2" color="text.secondary">Отзывов пока нет</Typography>
                    )}
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                        <TextField
                            label="Ваш отзыв"
                            value={newReview}
                            onChange={(e) => setNewReview(e.target.value)}
                            fullWidth
                            variant="outlined"
                            margin="normal"
                            multiline
                            maxRows={3}
                        />
                        <Button onClick={handleAddReview} variant="outlined">Оставить</Button>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseReviewDialog}>Закрыть</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={editingReviewOpen} onClose={() => setEditingReviewOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Редактирование отзыва</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <TextField
                        label="Отзыв"
                        value={editedReviewText}
                        onChange={(e) => setEditedReviewText(e.target.value)}
                        fullWidth
                        variant="outlined"
                        margin="normal"
                        multiline
                        rows={4}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleSaveEditedReview} variant="contained">Сохранить</Button>
                    <Button onClick={() => setEditingReviewOpen(false)}>Отмена</Button>
                </DialogActions>
            </Dialog>

            <Snackbar
                open={openSnackbar}
                autoHideDuration={3000}
                onClose={() => setOpenSnackbar(false)}
            >
                <Alert severity="success" onClose={() => setOpenSnackbar(false)}>
                    {snackbarMessage}
                </Alert>
            </Snackbar>
        </Box>
        </>
    );
};

export default BooksPage;
