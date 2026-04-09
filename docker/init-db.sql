-- Создание базы данных
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'soundgoodizerBD')
BEGIN
    CREATE DATABASE soundgoodizerBD;
END
GO

USE soundgoodizerBD;
GO

-- Таблица ролей
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='roles' AND xtype='U')
BEGIN
CREATE TABLE roles (
    role_id INT PRIMARY KEY IDENTITY(1,1),
    role_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255)
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
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
    email_verification_expires DATETIME,
    role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE()
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='brands' AND xtype='U')
BEGIN
CREATE TABLE brands (
    brand_id INT PRIMARY KEY IDENTITY(1,1),
    brand_name NVARCHAR(100) NOT NULL UNIQUE,
    country NVARCHAR(100),
    description NVARCHAR(2000),
    website NVARCHAR(500)
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='categories' AND xtype='U')
BEGIN
CREATE TABLE categories (
    category_id INT PRIMARY KEY IDENTITY(1,1),
    category_name NVARCHAR(100) NOT NULL UNIQUE,
    description NVARCHAR(1000),
    icon_class NVARCHAR(100)
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='instrument_conditions' AND xtype='U')
BEGIN
CREATE TABLE instrument_conditions (
    condition_id INT PRIMARY KEY IDENTITY(1,1),
    condition_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(500),
    discount_percentage FLOAT DEFAULT 0
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='instruments' AND xtype='U')
BEGIN
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
    condition_id INT FOREIGN KEY REFERENCES instrument_conditions(condition_id),
    quantity_in_stock INT DEFAULT 1,
    is_available_for_sale BIT DEFAULT 1,
    is_available_for_rent BIT DEFAULT 1,
    main_image_url NVARCHAR(500),
    created_by INT FOREIGN KEY REFERENCES users(user_id),
    created_at DATETIME DEFAULT GETDATE(),
    views_count INT DEFAULT 0
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='instrument_images' AND xtype='U')
BEGIN
CREATE TABLE instrument_images (
    image_id INT PRIMARY KEY IDENTITY(1,1),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    image_url NVARCHAR(500) NOT NULL,
    alt_text NVARCHAR(200),
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE()
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='order_statuses' AND xtype='U')
BEGIN
CREATE TABLE order_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    color_code NVARCHAR(7) DEFAULT '#6c757d'
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='purchase_orders' AND xtype='U')
BEGIN
CREATE TABLE purchase_orders (
    order_id INT PRIMARY KEY IDENTITY(1,1),
    order_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),
    quantity INT NOT NULL DEFAULT 1,
    unit_price FLOAT NOT NULL,
    total_price FLOAT NOT NULL,
    shipping_first_name NVARCHAR(50),
    shipping_last_name NVARCHAR(50),
    shipping_phone NVARCHAR(20),
    shipping_address NVARCHAR(500),
    shipping_city NVARCHAR(100),
    shipping_postal_code NVARCHAR(20),
    delivery_method NVARCHAR(50),
    delivery_cost FLOAT DEFAULT 0,
    status_id INT NOT NULL FOREIGN KEY REFERENCES order_statuses(status_id),
    order_date DATETIME DEFAULT GETDATE(),
    shipped_date DATETIME,
    delivered_date DATETIME,
    cancelled_date DATETIME
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='rental_statuses' AND xtype='U')
BEGIN
CREATE TABLE rental_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    color_code NVARCHAR(7) DEFAULT '#6c757d'
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='rental_orders' AND xtype='U')
BEGIN
CREATE TABLE rental_orders (
    rental_id INT PRIMARY KEY IDENTITY(1,1),
    rental_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),
    rental_start_date DATE NOT NULL,
    rental_end_date DATE NOT NULL,
    actual_return_date DATE,
    daily_price FLOAT NOT NULL,
    total_days AS DATEDIFF(day, rental_start_date, rental_end_date),
    deposit_amount FLOAT DEFAULT 0,
    total_amount FLOAT NOT NULL,
    delivery_address NVARCHAR(500),
    status_id INT NOT NULL FOREIGN KEY REFERENCES rental_statuses(status_id),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_rental_dates CHECK (rental_end_date > rental_start_date)
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='repair_statuses' AND xtype='U')
BEGIN
CREATE TABLE repair_statuses (
    status_id INT PRIMARY KEY IDENTITY(1,1),
    status_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255),
    sort_order INT DEFAULT 0
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='repair_requests' AND xtype='U')
BEGIN
CREATE TABLE repair_requests (
    request_id INT PRIMARY KEY IDENTITY(1,1),
    request_number NVARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    customer_instrument_name NVARCHAR(200) NOT NULL,
    brand NVARCHAR(100),
    model NVARCHAR(100),
    problem_description NVARCHAR(MAX) NOT NULL,
    problem_photos_urls NVARCHAR(MAX),
    assigned_to INT FOREIGN KEY REFERENCES users(user_id),
    actual_cost FLOAT,
    actual_completion_date DATE,
    status_id INT NOT NULL FOREIGN KEY REFERENCES repair_statuses(status_id),
    created_at DATETIME DEFAULT GETDATE(),
    completed_at DATETIME
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='deliveries' AND xtype='U')
BEGIN
CREATE TABLE deliveries (
    delivery_id INT PRIMARY KEY IDENTITY(1,1),
    delivery_number NVARCHAR(50) UNIQUE NOT NULL,
    order_id INT NULL FOREIGN KEY REFERENCES purchase_orders(order_id),
    rental_id INT NULL FOREIGN KEY REFERENCES rental_orders(rental_id),
    delivery_type NVARCHAR(20) NOT NULL,
    address_to NVARCHAR(500) NOT NULL,
    contact_person NVARCHAR(100),
    contact_phone NVARCHAR(20),
    delivery_status NVARCHAR(50) DEFAULT 'pending'
        CHECK (delivery_status IN ('pending','assigned','picked_up','in_transit','delivered','failed','cancelled')),
    scheduled_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_delivery_reference CHECK (
        (order_id IS NOT NULL AND rental_id IS NULL) OR
        (order_id IS NULL AND rental_id IS NOT NULL)
    )
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='reviews' AND xtype='U')
BEGIN
CREATE TABLE reviews (
    review_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),
    order_id INT NOT NULL FOREIGN KEY REFERENCES purchase_orders(order_id),
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title NVARCHAR(200),
    comment NVARCHAR(MAX) NOT NULL,
    is_approved BIT DEFAULT 0,
    moderated_by INT NULL FOREIGN KEY REFERENCES users(user_id),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_user_order_review UNIQUE (user_id, order_id)
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='review_photos' AND xtype='U')
BEGIN
CREATE TABLE review_photos (
    photo_id INT PRIMARY KEY IDENTITY(1,1),
    review_id INT NOT NULL FOREIGN KEY REFERENCES reviews(review_id) ON DELETE CASCADE,
    photo_url NVARCHAR(500) NOT NULL,
    alt_text NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE()
);
END
GO

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='cart_items' AND xtype='U')
BEGIN
CREATE TABLE cart_items (
    cart_item_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
    instrument_id INT NOT NULL FOREIGN KEY REFERENCES instruments(instrument_id),
    quantity INT NOT NULL DEFAULT 1,
    is_for_rental BIT DEFAULT 0,
    rental_start_date DATE NULL,
    rental_end_date DATE NULL,
    added_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_rental_dates_cart CHECK (
        (is_for_rental = 0 AND rental_start_date IS NULL AND rental_end_date IS NULL) OR
        (is_for_rental = 1 AND rental_start_date IS NOT NULL AND rental_end_date IS NOT NULL AND rental_end_date > rental_start_date)
    )
);
END
GO

-- Базовые данные (только если таблицы пустые)
IF NOT EXISTS (SELECT 1 FROM roles)
BEGIN
    INSERT INTO roles (role_name, description) VALUES
    ('admin', 'Администратор системы'),
    ('manager', 'Менеджер магазина'),
    ('technician', 'Мастер по ремонту'),
    ('customer', 'Покупатель');
END
GO

IF NOT EXISTS (SELECT 1 FROM order_statuses)
BEGIN
    INSERT INTO order_statuses (status_name, description, color_code) VALUES
    ('pending', 'Ожидает подтверждения', '#ffc107'),
    ('confirmed', 'Подтверждён', '#17a2b8'),
    ('processing', 'В обработке', '#007bff'),
    ('shipped', 'Отправлен', '#28a745'),
    ('delivered', 'Доставлен', '#20c997'),
    ('cancelled', 'Отменён', '#dc3545');
END
GO

IF NOT EXISTS (SELECT 1 FROM rental_statuses)
BEGIN
    INSERT INTO rental_statuses (status_name, description, color_code) VALUES
    ('reserved', 'Забронирован', '#ffc107'),
    ('active', 'Активная аренда', '#28a745'),
    ('completed', 'Завершена', '#20c997'),
    ('cancelled', 'Отменена', '#dc3545'),
    ('overdue', 'Просрочена', '#dc3545');
END
GO

IF NOT EXISTS (SELECT 1 FROM repair_statuses)
BEGIN
    INSERT INTO repair_statuses (status_name, description, sort_order) VALUES
    ('new', 'Новая заявка', 1),
    ('diagnosed', 'Диагностика завершена', 2),
    ('waiting_approval', 'Ожидает подтверждения', 3),
    ('approved', 'Подтверждена', 4),
    ('in_progress', 'В работе', 5),
    ('completed', 'Выполнена', 6),
    ('ready_for_pickup', 'Готова к выдаче', 7),
    ('cancelled', 'Отменена', 8);
END
GO

IF NOT EXISTS (SELECT 1 FROM instrument_conditions)
BEGIN
    INSERT INTO instrument_conditions (condition_name, description, discount_percentage) VALUES
    ('new', 'Новый, в оригинальной упаковке', 0),
    ('excellent', 'Отличное состояние', 5),
    ('very_good', 'Очень хорошее состояние', 10),
    ('good', 'Хорошее состояние', 15),
    ('fair', 'Удовлетворительное состояние', 25);
END
GO

-- Администратор по умолчанию (пароль: admin123)
IF NOT EXISTS (SELECT 1 FROM users)
BEGIN
    INSERT INTO users (login, email, password_hash, first_name, last_name, role_id, is_email_verified, is_active)
    VALUES ('admin', 'admin@soundgoodizer.ru', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Admin', 'Admin', 1, 1, 1);
END
GO
