import React from 'react';
import { Card, CardContent, Typography, Chip, Box } from '@mui/material';

const BookCard = ({ book }) => {
    return (
        <Card sx={{ width: 300, m: 2 }}>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    {book.title}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                    Автор: {book.author}
                </Typography>
                <Box sx={{ mt: 1 }}>
                    {book.categories && book.categories.map((genre, index) => (
                        <Chip key={index} label={genre} color="primary" sx={{ mr: 1, mb: 1 }} />
                    ))}
                </Box>
            </CardContent>
        </Card>
    );
};

export default BookCard;
