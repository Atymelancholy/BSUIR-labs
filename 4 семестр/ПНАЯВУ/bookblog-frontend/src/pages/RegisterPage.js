import React, { useState, useContext } from 'react';
import { Box, TextField, Button, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const RegisterPage = () => {

    const { login } = useContext(AuthContext);
    const navigate = useNavigate();
    const [form, setForm] = useState({ username: '', password: '' });
    const [error, setError] = useState('');

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/users/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });

            if (response.ok) {
                const userData = await response.json();
                login(userData); // Сохраняем в контекст
                navigate('/'); // Переход на главную
            } else {
                const errorData = await response.json();
                setError(errorData.message || 'Ошибка регистрации');
            }
        } catch (err) {
            setError('Ошибка сети');
        }
    };

    return (
        <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight="80vh"
            padding="2rem"
        >
            <Typography variant="h4" gutterBottom>
                Регистрация
            </Typography>

            <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '400px' }}>
                <TextField
                    fullWidth
                    margin="normal"
                    label="Имя пользователя"
                    name="username"
                    value={form.username}
                    onChange={handleChange}
                />
                <TextField
                    fullWidth
                    margin="normal"
                    label="Пароль"
                    name="password"
                    type="password"
                    value={form.password}
                    onChange={handleChange}
                />
                {error && (
                    <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                        {error}
                    </Typography>
                )}
                <Button fullWidth type="submit" variant="contained" color="primary" sx={{ mt: 2 }}>
                    Зарегистрироваться
                </Button>
            </form>
        </Box>
    );
};

export default RegisterPage;
