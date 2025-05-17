import axios from 'axios';

import API from 'http://localhost:8080/api';

export const getBooks = () => axios.get(`${API}/books`);
export const addBook = (book) => axios.post(`${API}/books`, book);
export const updateBook = (id, book) => axios.put(`${API}/books/${id}`, book);
export const deleteBook = (id) => axios.delete(`${API}/books/${id}`);
export const getCategories = () => axios.get(`${API}/categories`);

export const getUsers = () => API.get("/users");
export const createUser = (user) => API.post("/users", user);
export const updateUser = (id, user) => API.put(`/users/${id}`, user);
export const deleteUser = (id) => API.delete(`/users/${id}`);
export const getCategories = () => API.get("/categories");