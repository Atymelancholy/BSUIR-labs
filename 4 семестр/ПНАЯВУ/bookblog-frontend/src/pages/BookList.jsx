import { Table, Tag, Button, Popconfirm } from 'antd';
import { useEffect, useState } from 'react';
import api from '../services/api';

const BookList = ({ onEdit }) => {
    const [books, setBooks] = useState([]);

    useEffect(() => {
        api.get('/books').then(res => setBooks(res.data));
    }, []);

    const handleDelete = (bookId) => {
        api.delete(`/books/${bookId}`).then(() => {
            setBooks(books.filter(book => book.id !== bookId));
        }).catch(error => {
            console.error('Ошибка при удалении книги:', error);
        });
    };

    const columns = [
        {
            title: 'Название',
            dataIndex: 'title',
            key: 'title',
        },
        {
            title: 'Автор',
            dataIndex: 'author',
            key: 'author',
        },
        {
            title: 'Категории',
            dataIndex: 'categories',
            key: 'categories',
            render: (categories) => (
                <>
                    {categories.map(category => (
                        <Tag key={category.id}>{category.name}</Tag>
                    ))}
                </>
            ),
        },
        {
            title: 'Действия',
            key: 'actions',
            render: (_, book) => (
                <>
                    <Button onClick={() => onEdit(book)} style={{ marginRight: 8 }}>Редактировать</Button>
                    <Popconfirm
                        title="Вы уверены, что хотите удалить эту книгу?"
                        onConfirm={() => handleDelete(book.id)}
                        okText="Да"
                        cancelText="Нет"
                    >
                        <Button danger>Удалить</Button>
                    </Popconfirm>
                </>
            ),
        },
    ];

    return (
        <Table
            dataSource={books}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 5 }}
        />
    );
};

export default BookList;
