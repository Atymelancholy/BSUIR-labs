import React, { useContext, useEffect, useState } from 'react';
import {
    Typography, Box, Avatar, List, ListItem, ListItemText,
    Divider, Button, Dialog, DialogActions, DialogContent,
    DialogContentText, DialogTitle, TextField
} from '@mui/material';
import { AuthContext } from '../context/AuthContext';
import Header from '../components/Header';
import axios from 'axios';

const Profile = () => {
    const { user, logout, updateUser } = useContext(AuthContext);
    const [categories, setCategories] = useState([]);
    const [comments, setComments] = useState([]);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [editUsername, setEditUsername] = useState('');
    const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
    const [openBooksDialog, setOpenBooksDialog] = useState(false);
    const [selectedCategoryBooks, setSelectedCategoryBooks] = useState([]);
    const [selectedCategoryName, setSelectedCategoryName] = useState('');

    useEffect(() => {
        if (user?.id) {
            axios.get(`${process.env.REACT_APP_API_URL}/api/categories/user/${user.id}`)
                .then(res => setCategories(res.data))
                .catch(err => console.error("Ошибка при загрузке категорий", err));

            axios.get(`http://localhost:8080/api/responses/user/${user.id}`)
                .then(res => setComments(res.data))
                .catch(err => console.error("Ошибка при загрузке комментариев", err));
        }
    }, [user]);

    const handleDelete = () => {
        axios.delete(`${process.env.REACT_APP_API_URL}/api/users/${user.id}`)
            .then(() => {
                alert("Профиль успешно удалён");
                logout();
            })
            .catch(err => {
                console.error("Ошибка при удалении", err);
                alert("Не удалось удалить профиль");
            });
    };

    const handleUpdate = () => {
        axios.put(`${process.env.REACT_APP_API_URL}/api/users/${user.id}`, {
            ...user,
            username: editUsername,
        })
            .then(() => {
                updateUser({ username: editUsername });
                alert("Профиль обновлён");
                setEditDialogOpen(false);
            })
            .catch(err => {
                console.error("Ошибка при обновлении", err);
                alert("Не удалось обновить профиль");
            });
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

    if (!user) {
        return <Typography sx={{ p: 4 }}>Вы не авторизованы.</Typography>;
    }

    return (
        <>
            <Header />
            <Box sx={{ padding: 4 }}>
                <Typography variant="h4">Профиль</Typography>
                <Box mt={2} display="flex" alignItems="center" gap={2}>
                    <Avatar
                        alt="User Avatar"
                        src="/profile-placeholder.png"
                        sx={{ width: 80, height: 80 }}
                    />
                    <Box>
                        <Typography>Имя пользователя: {user.username}</Typography>
                        <Typography>ID: {user.id}</Typography>
                    </Box>
                </Box>

                <Box mt={3} display="flex" gap={2}>
                    <Button variant="outlined" color="primary" onClick={() => {
                        setEditUsername(user.username);
                        setEditDialogOpen(true);
                    }}>
                        Редактировать профиль
                    </Button>
                    <Button variant="outlined" color="error" onClick={() => setConfirmDeleteOpen(true)}>
                        Удалить профиль
                    </Button>
                </Box>

                <Divider sx={{ my: 4 }} />

                <Typography variant="h6">Предпочтения пользователя:</Typography>
                <List>
                    {categories.length > 0 ? (
                        categories.map((cat) => (
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
                            </ListItem>
                        ))
                    ) : (
                        <Typography color="text.secondary" sx={{ ml: 2 }}>Категории не найдены</Typography>
                    )}
                </List>

                <Divider sx={{ my: 4 }} />

                <Typography variant="h6">Комментарии пользователя:</Typography>
                <List>
                    {comments.length > 0 ? (
                        comments.map((comment) => (
                            <ListItem key={comment.id}>
                                <ListItemText primary={comment.content} />
                            </ListItem>
                        ))
                    ) : (
                        <Typography color="text.secondary" sx={{ ml: 2 }}>Комментариев пока нет</Typography>
                    )}
                </List>

                <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
                    <DialogTitle>Редактировать профиль</DialogTitle>
                    <DialogContent>
                        <TextField
                            autoFocus
                            margin="dense"
                            label="Имя пользователя"
                            type="text"
                            fullWidth
                            value={editUsername}
                            onChange={(e) => setEditUsername(e.target.value)}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setEditDialogOpen(false)}>Отмена</Button>
                        <Button onClick={handleUpdate}>Сохранить</Button>
                    </DialogActions>
                </Dialog>

                <Dialog open={confirmDeleteOpen} onClose={() => setConfirmDeleteOpen(false)}>
                    <DialogTitle>Удаление профиля</DialogTitle>
                    <DialogContent>
                        <DialogContentText>
                            Вы уверены, что хотите удалить свой профиль? Это действие необратимо.
                        </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setConfirmDeleteOpen(false)}>Отмена</Button>
                        <Button onClick={handleDelete} color="error">Удалить</Button>
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
            </Box>
        </>
    );
};

export default Profile;
