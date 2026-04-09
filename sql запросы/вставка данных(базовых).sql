INSERT INTO roles (role_name, description) VALUES
('admin', 'Администратор системы'),
('manager', 'Менеджер магазина'),
('technician', 'Мастер по ремонту'),
('customer', 'Клиент');
GO

INSERT INTO users (login, email, password_hash, first_name, last_name, middle_name, phone, role_id, is_email_verified) VALUES
('admin', 'e.saltymakov06@gmail.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Егор', 'Салтымаков', 'Максимович', '+7 (951) 587-89-41', 1, 1);
GO

-- статусы заказов на покупку
INSERT INTO order_statuses (status_name, description, color_code) VALUES
('pending', 'Ожидает подтверждения', '#ffc107'),
('confirmed', 'Подтвержден', '#17a2b8'),
('processing', 'В обработке', '#007bff'),
('shipped', 'Отправлен', '#28a745'),
('delivered', 'Доставлен', '#20c997'),
('cancelled', 'Отменен', '#dc3545');
GO

-- статусы аренды
INSERT INTO rental_statuses (status_name, description, color_code) VALUES
('reserved', 'Забронирован', '#ffc107'),
('active', 'Активная аренда', '#28a745'),
('completed', 'Завершена', '#20c997'),
('cancelled', 'Отменена', '#dc3545'),
('overdue', 'Просрочена', '#dc3545');
GO

-- статусы ремонта
INSERT INTO repair_statuses (status_name, description, sort_order) VALUES
('new', 'Новая заявка', 1),
('diagnosed', 'Диагностика завершена', 2),
('waiting_approval', 'Ожидает согласования', 3),
('approved', 'Согласовано', 4),
('in_progress', 'В работе', 5),
('completed', 'Завершен', 6),
('ready_for_pickup', 'Готов к выдаче', 7),
('cancelled', 'Отменен', 8);
GO

-- состояния инструментов
INSERT INTO instrument_conditions (condition_name, description, discount_percentage) VALUES
('new', 'Новый, в оригинальной упаковке', 0),
('excellent', 'Отличное состояние', 5),
('very_good', 'Очень хорошее состояние', 10),
('good', 'Хорошее состояние', 15),
('fair', 'Удовлетворительное состояние', 25);
GO

-- бренды инструментов
INSERT INTO brands (brand_name, country, description, website) VALUES
('Fender', 'USA', 'Американский производитель гитар и бас-гитар', 'https://www.fender.com'),
('Gibson', 'USA', 'Легендарный производитель гитар', 'https://www.gibson.com'),
('Yamaha', 'Japan', 'Японский производитель музыкальных инструментов', 'https://www.yamaha.com'),
('Roland', 'Japan', 'Производитель электронных музыкальных инструментов', 'https://www.roland.com'),
('Pearl', 'Japan', 'Производитель ударных установок', 'https://pearldrum.com'),
('Selmer', 'France', 'Французский производитель духовых инструментов', 'https://www.selmer.fr'),
('Ibanez', 'Japan', 'Производитель гитар и бас-гитар', 'https://www.ibanez.com'),
('Casio', 'Japan', 'Производитель цифровых пианино', 'https://www.casio.com'),
('Shure', 'USA', 'Производитель микрофонов', 'https://www.shure.com'),
('Taylor', 'USA', 'Производитель акустических гитар', 'https://www.taylorguitars.com');
GO

-- категории инструментов
INSERT INTO categories (category_name, description, icon_class) VALUES
('Электрогитары', 'Электрические гитары', 'fa-guitar-electric'),
('Акустические гитары', 'Акустические и классические гитары', 'fa-guitar-acoustic'),
('Бас-гитары', 'Бас-гитары', 'fa-guitar-bass'),
('Ударные установки', 'Барабанные установки и перкуссия', 'fa-drum'),
('Клавишные', 'Пианино, синтезаторы, цифровые пианино', 'fa-piano'),
('Духовые', 'Саксофоны, трубы, флейты', 'fa-music'),
('Микрофоны', 'Вокальные и инструментальные микрофоны', 'fa-microphone'),
('Усилители', 'Гитарные и басовые усилители', 'fa-volume-up');
GO

INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Fender Stratocaster American Professional II', 1, 1, 'American Professional II', 2023, 125000, 1500, 'Легендарная электрогитара с тремя синглами. Идеально подходит для рок, блюз и поп-музыки.', '3 сингла, тремоло, кленовый гриф, 22 лада', 1, 3),
('Gibson Les Paul Standard 50s', 2, 1, 'Standard 50s', 2022, 180000, 2000, 'Классическая гитара с хамбакерами. Тёплый и насыщенный звук.', '2 хамбакера, махагони, накладка из палисандра', 2, 1),
('Taylor 814ce', 10, 2, '814ce', 2023, 220000, 2500, 'Флагманская акустическая гитара с встроенным предусилителем. Отличный выбор для профессиональных музыкантов.', 'Ель ситхинская, палисандр, встроенный предусилитель Expression System 2', 1, 1),
('Yamaha C40 Classical Guitar', 3, 2, 'C40', 2023, 12000, 200, 'Классическая гитара для начинающих. Отличное качество по доступной цене.', 'Нейлоновые струны, липа, накладка из мербау', 1, 5),
('Fender Precision Bass', 1, 3, 'American Professional II', 2023, 135000, 1600, 'Классический бас для любой музыки. Стандарт в мире бас-гитар.', '1 сингл, ольха, 4 струны, 20 ладов', 1, 2),
('Pearl Export Drum Set', 5, 4, 'EXL725BR/C', 2023, 85000, 1200, 'Полная ударная установка для начинающих и продвинутых барабанщиков.', '5 барабанов (бас-барабан, томы, напольный том, малый барабан), 3 тарелки, железная фурнитура', 1, 2),
('Yamaha C3X Grand Piano', 3, 5, 'C3X PE', 2022, 4500000, 50000, 'Концертный рояль премиум-класса. Идеальный инструмент для концертных залов и студий.', '228 см, полированный чёрный, 88 клавиш', 1, 1),
('Roland Juno-DS88', 4, 5, 'Juno-DS88', 2023, 95000, 1100, '88-клавишный синтезатор с взвешенной клавиатурой. Более 1000 тембров.', 'Взвешенная клавиатура, 1000+ тембров, 256-голосная полифония', 1, 4),
('Selmer SAS280 Alto Saxophone', 6, 6, 'SAS280', 2020, 220000, 2500, 'Альтовый саксофон для профессионалов. Французское качество.', 'Латунь, золотое покрытие, высокая F# клавиша', 3, 1),
('Shure SM58', 9, 7, 'SM58', 2023, 8500, 150, 'Легендарный вокальный микрофон. Стандарт для живых выступлений.', 'Кардиоидная направленность, частотный диапазон 50Hz-15kHz', 1, 10);