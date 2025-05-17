import React, { useContext, useState } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Menu, MenuItem, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import bannerImage from '../assets/intro.jpg';
import profileIcon from '../assets/logo.png';
import { AuthContext } from '../context/AuthContext';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import Header from '../components/Header';

const HomePage = () => {
    const navigate = useNavigate();
    const { user, logout } = useContext(AuthContext);
    const [anchorEl, setAnchorEl] = useState(null);

    const openMenu = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const closeMenu = () => {
        setAnchorEl(null);
    };

    const goToUsers = () => {
        navigate('/users');
    };

    console.log("User value:", user);


    const goToBooks = () => {
        navigate('/books');
    };

    const goToCategories = () => {
        navigate('/categories');
    };

    const goToLogin = () => {
        navigate('/login');
    };

    const goToRegister = () => {
        navigate('/register');
    };

    const goToProfile = () => {
        navigate('/profile');
        closeMenu();
    };

    const handleLogout = () => {
        logout();
        closeMenu();
    };

    return (
        <>
            <Header />


            <Box
                sx={{
                    display: 'flex',
                    flexDirection: {xs: 'column', md: 'row'},
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: 'calc(100vh - 64px)',
                    backgroundColor: '#f4f4f4',
                    padding: '1rem',
                    gap: '1rem',
                    boxSizing: 'border-box',
                }}
            >
                <motion.div
                    initial={{opacity: 0, x: -50}}
                    animate={{opacity: 1, x: 0}}
                    transition={{duration: 0.8}}
                    style={{
                        flex: 1,
                        height: '90%',
                        borderRadius: '12px',
                        overflow: 'hidden',
                    }}
                >
                    <Box
                        sx={{
                            width: '100%',
                            height: '100%',
                            backgroundImage: `url(${bannerImage})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            borderRadius: '12px',
                        }}
                    />
                </motion.div>
                <motion.div
                    initial={{opacity: 0, x: 50}}
                    animate={{opacity: 1, x: 0}}
                    transition={{duration: 0.8, delay: 0.2}}
                    style={{flex: 1}}
                >
                    <Box
                        sx={{
                            maxWidth: '600px',
                            margin: '0 auto',
                            textAlign: 'left',
                        }}
                    >
                        <Typography
                            variant="h4"
                            gutterBottom
                            sx={{
                                fontFamily: '"Playfair Display", sans-serif',
                                fontWeight: 'normal',
                                fontSize: {xs: '1.5rem', md: '2.6rem'},
                                lineHeight: 1.6,
                                letterSpacing: '0.5px',
                                color: '#333',
                                textAlign: 'center'
                            }}
                        >
                            Добро пожаловать в мир книг, где каждый найдет свою историю!

                        </Typography>
                        <Typography
                            variant="h4"
                            gutterBottom
                            sx={{
                                fontFamily: '"Playfair Display", sans-serif',
                                fontWeight: 'normal',
                                fontSize: {xs: '1.5rem', md: '2.6rem'},
                                lineHeight: 1.6,
                                letterSpacing: '0.5px',
                                color: '#333',
                                textAlign: 'center'
                            }}
                        >
                            Откройте новые горизонты и поделитесь своими впечатлениями!
                        </Typography>
                    </Box>
                </motion.div>

            </Box>
        </>
    );
};

export default HomePage;
