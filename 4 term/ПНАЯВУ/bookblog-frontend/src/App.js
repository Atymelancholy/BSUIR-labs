import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import BooksPage from './pages/BooksPage';
import { AuthProvider } from './context/AuthContext';
import Profile from './pages/Profile';
import RegisterPage from './pages/RegisterPage';
import CategoryList from './pages/CategoryList';

const App = () => {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/categories" element={<CategoryList />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/books" element={<BooksPage />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
};

export default App;
