import { Tag, Popconfirm } from 'antd';
import api from '../services/api';

const CategoryTag = ({ bookId, category, onRemove }) => {
    const handleRemove = () => {
        api.delete(`/books/${bookId}/categories/${category.id}`)
            .then(() => onRemove(category.id));
    };

    return (
        <Popconfirm title="Удалить категорию?" onConfirm={handleRemove}>
            <Tag closable>{category.name}</Tag>
        </Popconfirm>
    );
};