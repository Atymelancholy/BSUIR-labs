// components/Header.js
import React, { useContext, useState } from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box,
    Menu,
    MenuItem,
    IconButton,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import profileIcon from '../assets/logo.png';
import { AuthContext } from '../context/AuthContext';

const Header = () => {
    const navigate = useNavigate();
    const { user, logout } = useContext(AuthContext);
    const [anchorEl, setAnchorEl] = useState(null);

    const openMenu = (event) => setAnchorEl(event.currentTarget);
    const closeMenu = () => setAnchorEl(null);

    const goToLogin = () => navigate('/login');
    const goToRegister = () => navigate('/register');
    const goToProfile = () => {
        navigate('/profile');
        closeMenu();
    };
    const handleLogout = () => {
        logout();
        closeMenu();
    };

    const goToBooks = () => navigate('/books');
    const goToCategories = () => navigate('/categories');

    return (
        <AppBar position="static" color="default" elevation={2}>
            <Toolbar sx={{ justifyContent: 'space-between' }}>
                <Typography
                    variant="h3"
                    component="div"
                    onClick={() => navigate('/')}
                    sx={{
                        fontWeight: 'bold',
                        fontFamily: '"Playfair Display", sans-serif',
                        cursor: 'pointer',
                        transition: 'color 0.3s',
                        '&:hover': {
                            color: '#71a372',
                        },
                    }}
                >
                    Bookling
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <Button color="inherit" onClick={goToBooks}>
                        Список книг
                    </Button>
                    <Button color="inherit" onClick={goToCategories}>
                        Категории
                    </Button>

                    {user ? (
                        <>
                            <IconButton color="inherit" onClick={openMenu}>
                                <img
                                    src={profileIcon}
                                    alt="Профиль"
                                    style={{
                                        width: '45px',
                                        height: '45px',
                                        borderRadius: '50%',
                                    }}
                                />
                            </IconButton>
                            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={closeMenu}>
                                <MenuItem onClick={goToProfile}>Профиль</MenuItem>
                                <MenuItem onClick={handleLogout}>Выход</MenuItem>
                            </Menu>
                        </>
                    ) : (
                        <>
                            <Button color="inherit" onClick={goToLogin}>
                                Вход
                            </Button>
                            <Button color="inherit" onClick={goToRegister}>
                                Регистрация
                            </Button>
                        </>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Header;
