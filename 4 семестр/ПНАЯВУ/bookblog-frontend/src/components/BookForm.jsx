import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { List, ListItem, ListItemText, Typography } from '@mui/material';

const CategoryList = () => {
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/categories')
            .then((response) => {
                setCategories(response.data);
                setLoading(false);
            })
            .catch((error) => {
                console.error('Ошибка при получении категорий:', error);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <Typography>Загрузка категорий...</Typography>;
    }

    return (
        <div>
            <Typography variant="h4" gutterBottom>
                Категории
            </Typography>
            <List>
                {categories.length === 0 ? (
                    <Typography>Нет категорий для отображения</Typography>
                ) : (
                    categories.map((category) => (
                        <ListItem key={category.id}>
                            <ListItemText primary={category.name} />
                        </ListItem>
                    ))
                )}
            </List>
        </div>
    );
};

export default CategoryList;