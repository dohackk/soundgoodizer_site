CREATE INDEX idx_users_login ON users(login);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);

CREATE INDEX idx_instruments_brand ON instruments(brand_id);
CREATE INDEX idx_instruments_category ON instruments(category_id);
CREATE INDEX idx_instruments_condition ON instruments(condition_id);
CREATE INDEX idx_instruments_price ON instruments(purchase_price);
CREATE INDEX idx_instruments_available_sale ON instruments(is_available_for_sale) WHERE is_available_for_sale = 1;
CREATE INDEX idx_instruments_available_rent ON instruments(is_available_for_rent) WHERE is_available_for_rent = 1;

CREATE INDEX idx_purchase_orders_user ON purchase_orders(user_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status_id);
CREATE INDEX idx_purchase_orders_date ON purchase_orders(order_date);

CREATE INDEX idx_rental_orders_user ON rental_orders(user_id);
CREATE INDEX idx_rental_orders_instrument ON rental_orders(instrument_id);
CREATE INDEX idx_rental_orders_dates ON rental_orders(rental_start_date, rental_end_date);

CREATE INDEX idx_repair_requests_user ON repair_requests(user_id);
CREATE INDEX idx_repair_requests_status ON repair_requests(status_id);

CREATE INDEX idx_reviews_instrument ON reviews(instrument_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_approved ON reviews(is_approved) WHERE is_approved = 1;

CREATE INDEX idx_cart_items_user ON cart_items(user_id);