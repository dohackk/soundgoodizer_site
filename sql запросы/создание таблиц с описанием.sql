-- Таблица ролей пользователей
CREATE TABLE roles (
    role_id INT PRIMARY KEY IDENTITY(1,1),
    role_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255)
);
GO

-- Таблица пользователей
CREATE TABLE users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    login NVARCHAR(50) NOT NULL UNIQUE,  
    email NVARCHAR(100) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL, 
    first_name NVARCHAR(50) NOT NULL,
    last_name NVARCHAR(50) NOT NULL,
    middle_name NVARCHAR(50),
    phone NVARCHAR(20),
    address NVARCHAR(500),
    city NVARCHAR(100),
    postal_code NVARCHAR(20),
    avatar_url NVARCHAR(500),
    
    is_email_verified BIT DEFAULT 0,  
    email_verification_code NVARCHAR(10),  
    email_verification_expires DATETIME,  -- Срок действия кода

    role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
    is_active BIT DEFAULT 1, 
    
    created_at DATETIME DEFAULT GETDATE() 
);
GO

-- Таблица брендов инструментов
CREATE TABLE brands (
    brand_id INT PRIMARY KEY IDENTITY(1,1),
    brand_name NVARCHAR(100) NOT NULL UNIQUE, 
    country NVARCHAR(100), 
    description NVARCHAR(2000),
    website NVARCHAR(500)  
);
GO

-- Таблица категорий инструментов
CREATE TABLE categories (
    category_id INT PRIMARY KEY IDENTITY(1,1),
    category_name NVARCHAR(100) NOT NULL UNIQUE,  
    description NVARCHAR(1000),
    icon_class NVARCHAR(100)
);
GO

-- Таблица состояний инструментов
CREATE TABLE instrument_conditions (
    condition_id INT PRIMARY KEY IDENTITY(1,1),
    condition_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(500),
    discount_percentage FLOAT DEFAULT 0  -- Скидка за состояние (в процентах)
);
GO

-- Основная таблица музыкальных инструментов
CREATE TABLE instruments (
    instrument_id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(200) NOT NULL,
    brand_id INT NOT NULL FOREIGN KEY REFERENCES brands(brand_id),
    category_id INT NOT NULL FOREIGN KEY REFERENCES categories(category_id),
    model NVARCHAR(100),
    year_of_manufacture INT,
    purchase_price FLOAT NOT NULL,
    rental_price_per_day FLOAT,
    rental_price_per_week FLOAT,
    rental_price_per_month FLOAT,
    description NVARCHAR(MAX),
    characteristics NVARCHAR(MAX),
    condition_id INT FOREIGN KEY REFERENCES instrument_conditions(condition_id),  -- Состояние
    quantity_in_stock INT DEFAULT 1,  -- Количество на складе
    is_available_for_sale BIT DEFAULT 1,
    is_available_for_rent BIT DEFAULT 1,
    main_image_url NVARCHAR(500),
    created_by INT FOREIGN KEY REFERENCES users(user_id),
    created_at DATETIME DEFAULT GETDATE(),
    views_count INT DEFAULT 0 
);
GO

-- Таблица дополнительных изображений инструментов
CREATE TABLE instrument_images (
    image_id INT PRIMARY KEY IDENTITY(1,1),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    image_url NVARCHAR(500) NOT NULL,
    alt_text NVARCHAR(200),
    sort_order INT DEFAULT 0,  -- Порядок показа (0, 1, 2...)
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Таблица статусов заказов на покупку
CREATE TABLE order_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    color_code NVARCHAR(7) DEFAULT '#6c757d'
);
GO

-- Таблица заказов на покупку
CREATE TABLE purchase_orders (
    order_id INT PRIMARY KEY IDENTITY(1,1),
    order_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),
    quantity INT NOT NULL DEFAULT 1,  -- Количество
    unit_price FLOAT NOT NULL,  -- Цена за единицу на момент заказа
    total_price FLOAT NOT NULL,  -- Общая сумма (unit_price * quantity)

    shipping_first_name NVARCHAR(50),
    shipping_last_name NVARCHAR(50),
    shipping_phone NVARCHAR(20),
    shipping_address NVARCHAR(500),
    shipping_city NVARCHAR(100),
    shipping_postal_code NVARCHAR(20),

    delivery_method NVARCHAR(50),
    delivery_cost FLOAT DEFAULT 0,
    
    status_id INT NOT NULL FOREIGN KEY REFERENCES order_statuses(status_id),
    
    order_date DATETIME DEFAULT GETDATE(),  -- Дата заказа
    shipped_date DATETIME,  -- Дата отправки
    delivered_date DATETIME,  -- Дата доставки
    cancelled_date DATETIME  -- Дата отмены
);
GO

-- Таблица статусов аренды
CREATE TABLE rental_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    color_code NVARCHAR(7) DEFAULT '#6c757d'
);
GO

-- Таблица заказов на аренду инструментов
CREATE TABLE rental_orders (
    rental_id INT PRIMARY KEY IDENTITY(1,1),
    rental_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),  -- Что арендуется
    
    rental_start_date DATE NOT NULL,
    rental_end_date DATE NOT NULL,
    actual_return_date DATE,  -- Фактическая дата возврата
    
    -- Цены и расчеты
    daily_price FLOAT NOT NULL,
    total_days AS DATEDIFF(day, rental_start_date, rental_end_date),
    subtotal FLOAT NOT NULL,  -- Сумма без залога (daily_price * total_days)
    deposit_amount FLOAT DEFAULT 0,  -- Сумма залога
    total_amount FLOAT NOT NULL,  -- Итоговая сумма (subtotal + deposit)
    
    delivery_address NVARCHAR(500),
    return_address NVARCHAR(500),  -- Адрес возврата
    delivery_notes NVARCHAR(1000),  -- Примечания по доставке
    
    status_id INT NOT NULL FOREIGN KEY REFERENCES rental_statuses(status_id),
    created_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT CHK_rental_dates CHECK (rental_end_date > rental_start_date)
);
GO

-- Таблица статусов ремонта
CREATE TABLE repair_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    sort_order INT DEFAULT 0
);
GO

-- Таблица заявок на ремонт инструментов
CREATE TABLE repair_requests (
    request_id INT PRIMARY KEY IDENTITY(1,1),
    request_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    
    -- Информация об инструменте для ремонта
    customer_instrument_name NVARCHAR(200) NOT NULL,  -- Название инструмента от клиента
    brand NVARCHAR(100),
    model NVARCHAR(100),
    
    problem_description NVARCHAR(MAX) NOT NULL,
    problem_photos_urls NVARCHAR(MAX),
    
    assigned_to INT FOREIGN KEY REFERENCES users(user_id),  -- Кому назначен ремонт (мастер)
    actual_cost FLOAT,  -- Фактическая стоимость
    actual_completion_date DATE,  -- Фактическая дата завершения
    
    status_id INT NOT NULL FOREIGN KEY REFERENCES repair_statuses(status_id),
    
    created_at DATETIME DEFAULT GETDATE(),
    completed_at DATETIME
);
GO

-- Таблица доставок (отслеживание доставок для покупок и аренд)
CREATE TABLE deliveries (
    delivery_id INT PRIMARY KEY IDENTITY(1,1),
    delivery_number NVARCHAR(50) UNIQUE NOT NULL,
    
    -- Ссылка на заказ или аренду (только одна из двух)
    order_id INT NULL FOREIGN KEY REFERENCES purchase_orders(order_id),
    rental_id INT NULL FOREIGN KEY REFERENCES rental_orders(rental_id),
    
    delivery_type NVARCHAR(20) NOT NULL,
    
    address_to NVARCHAR(500) NOT NULL,
    
    contact_person NVARCHAR(100),
    contact_phone NVARCHAR(20),
    
    delivery_status NVARCHAR(50) DEFAULT 'pending' 
        CHECK (delivery_status IN ('pending', 'assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'cancelled')),

    scheduled_date DATE,  -- Запланированная дата
    created_at DATETIME DEFAULT GETDATE()
    
    CONSTRAINT CHK_delivery_reference CHECK (
        (order_id IS NOT NULL AND rental_id IS NULL) OR 
        (order_id IS NULL AND rental_id IS NOT NULL)
    )
);
GO

-- Таблица отзывов (оставляются только после покупки, ссылаются на заказ)
CREATE TABLE reviews (
    review_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),  -- Кто оставил отзыв
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),  -- На какой инструмент
    order_id INT NOT NULL FOREIGN KEY REFERENCES purchase_orders(order_id),  -- По какому заказу
    
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),  -- Оценка от 1 до 5
    title NVARCHAR(200),  -- Заголовок отзыва
    comment NVARCHAR(MAX) NOT NULL,  -- Текст отзыва
    
    is_approved BIT DEFAULT 0,  -- Одобрен ли отзыв модератором
    moderated_by INT NULL FOREIGN KEY REFERENCES users(user_id),  -- Кто проверил
    
    created_at DATETIME DEFAULT GETDATE(),
    
    -- Уникальное ограничение: один отзыв на заказ
    CONSTRAINT UQ_user_order_review UNIQUE (user_id, order_id)
);
GO

-- Таблица фотографий к отзывам
CREATE TABLE review_photos (
    photo_id INT PRIMARY KEY IDENTITY(1,1),
    review_id INT NOT NULL FOREIGN KEY REFERENCES reviews(review_id) ON DELETE CASCADE,
    photo_url NVARCHAR(500) NOT NULL,
    alt_text NVARCHAR(200),  -- Описание фото
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Таблица корзины покупок
CREATE TABLE cart_items (
    cart_item_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),  -- Чья корзина
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),  -- Что в корзине
    quantity INT NOT NULL DEFAULT 1,  -- Количество
    
    -- Для аренды в корзине
    is_for_rental BIT DEFAULT 0,  -- 0 = покупка, 1 = аренда
    rental_start_date DATE NULL,
    rental_end_date DATE NULL,
    
    added_at DATETIME DEFAULT GETDATE(),  -- Когда добавлено в корзину
    
    -- Проверка: если аренда, то должны быть указаны даты
    CONSTRAINT CHK_rental_dates_cart CHECK (
        (is_for_rental = 0 AND rental_start_date IS NULL AND rental_end_date IS NULL) OR
        (is_for_rental = 1 AND rental_start_date IS NOT NULL AND rental_end_date IS NOT NULL AND rental_end_date > rental_start_date)
    )
);
GO