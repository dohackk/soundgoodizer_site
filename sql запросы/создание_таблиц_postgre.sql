-- =====================================================
-- Миграция SoundGoodizer: SQL Server → PostgreSQL
-- Выполнить в PostgreSQL (например, через psql или pgAdmin)
-- =====================================================

-- Роли
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    phone VARCHAR(20),
    address VARCHAR(500),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    avatar_url VARCHAR(500),
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verification_code VARCHAR(10),
    email_verification_expires TIMESTAMP,
    role_id INT NOT NULL REFERENCES roles(role_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Бренды
CREATE TABLE IF NOT EXISTS brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100),
    description VARCHAR(2000),
    website VARCHAR(500)
);

-- Категории
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(1000),
    icon_class VARCHAR(100)
);

-- Состояния инструментов
CREATE TABLE IF NOT EXISTS instrument_conditions (
    condition_id SERIAL PRIMARY KEY,
    condition_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(500),
    discount_percentage FLOAT DEFAULT 0
);

-- Инструменты
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    brand_id INT NOT NULL REFERENCES brands(brand_id),
    category_id INT NOT NULL REFERENCES categories(category_id),
    model VARCHAR(100),
    year_of_manufacture INT,
    purchase_price FLOAT NOT NULL,
    rental_price_per_day FLOAT,
    rental_price_per_week FLOAT,
    rental_price_per_month FLOAT,
    description TEXT,
    characteristics TEXT,
    condition_id INT REFERENCES instrument_conditions(condition_id),
    quantity_in_stock INT DEFAULT 1,
    is_available_for_sale BOOLEAN DEFAULT TRUE,
    is_available_for_rent BOOLEAN DEFAULT TRUE,
    main_image_url VARCHAR(500),
    created_by INT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    views_count INT DEFAULT 0
);

-- Изображения инструментов
CREATE TABLE IF NOT EXISTS instrument_images (
    image_id SERIAL PRIMARY KEY,
    instrument_id INT NOT NULL REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(200),
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Статусы заказов на покупку
CREATE TABLE IF NOT EXISTS order_statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    color_code VARCHAR(7) DEFAULT '#6c757d'
);

-- Заказы на покупку
CREATE TABLE IF NOT EXISTS purchase_orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL REFERENCES users(user_id),
    instrument_id INT NOT NULL REFERENCES instruments(instrument_id),
    quantity INT NOT NULL DEFAULT 1,
    unit_price FLOAT NOT NULL,
    total_price FLOAT NOT NULL,
    shipping_first_name VARCHAR(50),
    shipping_last_name VARCHAR(50),
    shipping_phone VARCHAR(20),
    shipping_address VARCHAR(500),
    shipping_city VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    delivery_method VARCHAR(50),
    delivery_cost FLOAT DEFAULT 0,
    status_id INT NOT NULL REFERENCES order_statuses(status_id),
    order_date TIMESTAMP DEFAULT NOW(),
    shipped_date TIMESTAMP,
    delivered_date TIMESTAMP,
    cancelled_date TIMESTAMP
);

-- Статусы аренды
CREATE TABLE IF NOT EXISTS rental_statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    color_code VARCHAR(7) DEFAULT '#6c757d'
);

-- Заказы на аренду
CREATE TABLE IF NOT EXISTS rental_orders (
    rental_id SERIAL PRIMARY KEY,
    rental_number VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL REFERENCES users(user_id),
    instrument_id INT NOT NULL REFERENCES instruments(instrument_id),
    rental_start_date DATE NOT NULL,
    rental_end_date DATE NOT NULL,
    actual_return_date DATE,
    daily_price FLOAT NOT NULL,
    total_days INT GENERATED ALWAYS AS (rental_end_date - rental_start_date) STORED,
    deposit_amount FLOAT DEFAULT 0,
    total_amount FLOAT NOT NULL,
    delivery_address VARCHAR(500),
    status_id INT NOT NULL REFERENCES rental_statuses(status_id),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_rental_dates CHECK (rental_end_date > rental_start_date)
);

-- Статусы ремонта
CREATE TABLE IF NOT EXISTS repair_statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    sort_order INT DEFAULT 0
);

-- Заявки на ремонт
CREATE TABLE IF NOT EXISTS repair_requests (
    request_id SERIAL PRIMARY KEY,
    request_number VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL REFERENCES users(user_id),
    customer_instrument_name VARCHAR(200) NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(100),
    problem_description TEXT NOT NULL,
    problem_photos_urls TEXT,
    assigned_to INT REFERENCES users(user_id),
    actual_cost FLOAT,
    actual_completion_date DATE,
    status_id INT NOT NULL REFERENCES repair_statuses(status_id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Отзывы
CREATE TABLE IF NOT EXISTS reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    instrument_id INT NOT NULL REFERENCES instruments(instrument_id),
    order_id INT NOT NULL REFERENCES purchase_orders(order_id),
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(200),
    comment TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    moderated_by INT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_user_order_review UNIQUE (user_id, order_id)
);

-- Фото отзывов
CREATE TABLE IF NOT EXISTS review_photos (
    photo_id SERIAL PRIMARY KEY,
    review_id INT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    photo_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Корзина
CREATE TABLE IF NOT EXISTS cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    instrument_id INT NOT NULL REFERENCES instruments(instrument_id),
    quantity INT NOT NULL DEFAULT 1,
    is_for_rental BOOLEAN DEFAULT FALSE,
    rental_start_date DATE,
    rental_end_date DATE,
    added_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_rental_dates_cart CHECK (
        (is_for_rental = FALSE AND rental_start_date IS NULL AND rental_end_date IS NULL)
        OR
        (is_for_rental = TRUE AND rental_start_date IS NOT NULL AND rental_end_date IS NOT NULL AND rental_end_date > rental_start_date)
    )
);

-- Доставки
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id SERIAL PRIMARY KEY,
    delivery_number VARCHAR(50) NOT NULL UNIQUE,
    order_id INT REFERENCES purchase_orders(order_id),
    rental_id INT REFERENCES rental_orders(rental_id),
    delivery_type VARCHAR(20) NOT NULL,
    address_to VARCHAR(500) NOT NULL,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    delivery_status VARCHAR(50) DEFAULT 'pending' CHECK (delivery_status IN ('pending','assigned','picked_up','in_transit','delivered','failed','cancelled')),
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_delivery_reference CHECK (
        (order_id IS NOT NULL AND rental_id IS NULL) OR
        (order_id IS NULL AND rental_id IS NOT NULL)
    )
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_instruments_brand ON instruments(brand_id);
CREATE INDEX IF NOT EXISTS idx_instruments_category ON instruments(category_id);
CREATE INDEX IF NOT EXISTS idx_instruments_condition ON instruments(condition_id);
CREATE INDEX IF NOT EXISTS idx_instruments_price ON instruments(purchase_price);
CREATE INDEX IF NOT EXISTS idx_instruments_available_sale ON instruments(is_available_for_sale) WHERE is_available_for_sale = TRUE;
CREATE INDEX IF NOT EXISTS idx_instruments_available_rent ON instruments(is_available_for_rent) WHERE is_available_for_rent = TRUE;
CREATE INDEX IF NOT EXISTS idx_purchase_orders_user ON purchase_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_rental_orders_user ON rental_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_rental_orders_instrument ON rental_orders(instrument_id);
CREATE INDEX IF NOT EXISTS idx_rental_orders_dates ON rental_orders(rental_start_date, rental_end_date);
CREATE INDEX IF NOT EXISTS idx_repair_requests_user ON repair_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_repair_requests_status ON repair_requests(status_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user ON cart_items(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_instrument ON reviews(instrument_id);
CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews(is_approved) WHERE is_approved = TRUE;
