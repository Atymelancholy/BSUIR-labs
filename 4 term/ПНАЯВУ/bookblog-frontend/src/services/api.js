import axios from 'axios';

// Настройка базового URL для бэкенда
const api = axios.create({
    baseURL: 'http://localhost:8080/api', // Укажите URL вашего Spring Boot-приложения
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавьте перехватчики (interceptors) при необходимости
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('Ошибка запроса:', error);
        return Promise.reject(error);
    }
);

export default api;