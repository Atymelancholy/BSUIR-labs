import React, { useState, useContext } from 'react';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const LoginPage = () => {
    const navigate = useNavigate();
    const { login } = useContext(AuthContext);

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch(`${process.env.REACT_APP_API_URL}/api/users/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const userData = await response.json();
                login(userData);
                navigate('/');
            } else {
                setErrorMessage('Неверные данные для входа.');
            }
        } catch (error) {
            console.error('Ошибка при входе:', error);
            setErrorMessage('Ошибка при подключении к серверу.');
        }
    };

    return (
        <Box sx={{ width: 300, margin: '0 auto', paddingTop: '50px' }}>
            <Typography variant="h4" gutterBottom align="center">
                Вход
            </Typography>
            {errorMessage && (
                <Typography color="error" variant="body2" align="center" gutterBottom>
                    {errorMessage}
                </Typography>
            )}
            <form onSubmit={handleLogin}>
                <TextField
                    label="Логин"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <TextField
                    label="Пароль"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <Button variant="contained" color="primary" fullWidth type="submit">
                    Войти
                </Button>
            </form>
        </Box>
    );
};

export default LoginPage;

