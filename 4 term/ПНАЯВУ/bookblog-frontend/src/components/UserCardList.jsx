// src/components/UserCardList.jsx
import React from 'react';
import {
    Card, CardContent, Typography, Box, Button, Chip,
} from '@mui/material';

const UserCardList = ({ users, onEdit, onDelete }) => (
    <>
        {users.map(user => (
            <Card
                key={user.id}
                variant="outlined"
                sx={{ borderRadius: 3, boxShadow: 2, marginBottom: 2 }}
            >
                <CardContent>
                    <Typography variant="h6">{user.username}</Typography>

                    <Typography variant="body2" sx={{ marginTop: 1 }}>Категории:</Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', marginTop: 1 }}>
                        {user.categories?.map(cat => (
                            <Chip key={cat.id} label={cat.name} color="primary" />
                        ))}
                    </Box>

                    <Box sx={{ marginTop: 2, display: 'flex', gap: 1 }}>
                        <Button variant="contained" size="small" onClick={() => onEdit(user.id)}>
                            ✏️ Редактировать
                        </Button>
                        <Button variant="outlined" size="small" color="error" onClick={() => onDelete(user.id)}>
                            🗑️ Удалить
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        ))}
    </>
);

export default UserCardList;
