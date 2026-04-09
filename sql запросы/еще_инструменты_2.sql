-- Электрогитары (category_id = 1)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Rickenbacker 330', 26, 1, '330 Fireglo', 2022, 290000, 3500, 'Тот самый "звонкий" звук британского вторжения.', 'Полуакустика, 2 сингла Hi-gain', 1, 1),
('Schecter Hellraiser C-1', 27, 1, 'Hellraiser', 2023, 98000, 1100, 'Мощная гитара для экстремальных жанров.', 'Махагони, активные EMG 81-TW/89', 1, 4),
('Fender Stratocaster Ultra', 1, 1, 'American Ultra', 2023, 245000, 2800, 'Самый современный и удобный Стратокастер.', 'Бесшумные датчики Ultra Noiseless', 1, 2),
('Gibson Les Paul Studio', 2, 1, 'Studio Smokehouse', 2022, 135000, 1500, 'Все достоинства Лес Пола без лишних украшений.', 'Махагони, кленовый топ, 490R/498T', 2, 3),
('Ibanez JEM Junior', 7, 1, 'Steve Vai Sig', 2023, 58000, 700, 'Подписная модель Стива Вая с ручкой "Monkey Grip".', 'Тремоло Double Locking, гриф Wizard III', 1, 5),
('Jackson King V', 19, 1, 'JS Series', 2023, 35000, 450, 'Агрессивная форма для настоящего металла.', 'Корпус тополь, амарантовая накладка', 1, 6);

-- Акустические гитары (category_id = 2)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Taylor 814ce', 10, 2, 'V-Class', 2022, 450000, 5000, 'Флагманская модель Taylor с невероятным резонансом.', 'Массив палисандра, ель Sitka', 1, 1),
('Yamaha APX600', 3, 2, 'Thinline', 2023, 42000, 500, 'Тонкий корпус, удобный для игры на сцене.', 'Встроенный тюнер и эквалайзер', 1, 8),
('Fender Newporter Player', 1, 2, 'California Series', 2023, 48000, 550, 'Яркая гитара с головой грифа как у электрогитары.', 'Ель, махагони, эксклюзивные цвета', 1, 4),
('Ibanez Talman', 7, 2, 'TCY10E', 2022, 28000, 350, 'Гибрид акустики и электрогитары.', 'Магнитный звукосниматель под грифом', 2, 5);

-- Бас-гитары (category_id = 3)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Rickenbacker 4003', 26, 3, '4003 Jetglo', 2023, 310000, 3800, 'Легендарный бас с уникальным панчем.', 'Сквозной гриф, стерео-выход Ric-O-Sound', 1, 1),
('Warwick Corvette $$', 36, 3, 'RockBass', 2023, 95000, 1100, 'Два мощных хамбакера и немецкая эргономика.', 'Ясень, клен, датчики MEC', 1, 2),
('Schecter Stiletto Extreme', 27, 3, 'Stiletto', 2023, 55000, 650, 'Удобный активный бас для долгой игры.', 'Топ из стеганого клена, активный EQ', 1, 4),
('Fender Precision Bass 50s', 1, 3, 'Vintera', 2022, 125000, 1400, 'Винтажный вайб золотой эры рок-н-ролла.', 'Толстый гриф профиля "C", анодированный пикгард', 2, 2);

-- Ударные (category_id = 4)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Ludwig Classic Maple', 28, 4, 'Fab 22', 2022, 320000, 4500, 'Выбор профессионалов для студийной записи.', '7 слоев клена, без хардвера', 1, 1),
('Sabian HHX Complex Set', 29, 4, 'HHX Performance', 2023, 145000, 2000, 'Темные, сложные и музыкальные тарелки.', 'B20 бронза, ручная ковка', 1, 2),
('Tama Iron Cobra 900', 22, 4, 'Power Glide', 2023, 28000, 350, 'Самая надежная педаль для бас-барабана.', 'Двойная цепь, кейс в комплекте', 1, 10),
('Roland SPD-SX PRO', 4, 4, 'Sampling Pad', 2023, 115000, 1500, 'Главный инструмент для запуска семплов на сцене.', '9 пэдов, большой цветной экран', 1, 3);

-- Клавишные (category_id = 5)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Moog Subsequent 37', 30, 5, 'Analog Synth', 2023, 195000, 2500, 'Жирный аналоговый звук от дедушки Муга.', 'Парафонический, 2 осциллятора, лестничный фильтр', 1, 2),
('Arturia PolyBrute', 31, 5, 'Matrix Synth', 2022, 280000, 3200, 'Морфинг звука и мощнейшая матрица модуляции.', '6 голосов, контроллер Morphée', 1, 1),
('Korg SV-2 88', 12, 5, 'Stage Vintage', 2023, 215000, 2400, 'Ретро-дизайн и лучшие звуки электропиано.', 'Ламповый преамп, 88 клавиш RH3', 1, 2),
('Moog Grandmother', 30, 5, 'Semi-Modular', 2023, 110000, 1300, 'Полумодульный синтезатор со встроенным ревербератором.', '100% аналог, пружинный ревер', 1, 3);

-- Микрофоны и оборудование (category_id = 7 и 8)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('AKG C414 XLS', 32, 7, 'Studio Classic', 2023, 105000, 1300, 'Один из самых универсальных микрофонов в мире.', '9 диаграмм направленности', 1, 4),
('Audio-Technica AT2020', 33, 7, 'Cardioid Condenser', 2023, 12000, 200, 'Стандарт для домашних студий.', 'Кардиоида, широкий динам. диапазон', 1, 25),
('Vox AC30C2', 34, 8, 'Custom Series', 2022, 145000, 1800, 'Тот самый звук Queen и The Beatles.', '30 Вт, 2x12" Celestion Greenback', 1, 2),
('Mesa/Boogie Dual Rectifier', 35, 8, 'Solo Head', 2021, 285000, 3500, 'Икона хай-гейн звука 2000-х.', '100 Вт, 3 канала, ламповое выпрямление', 3, 1),
('Behringer X32', 24, 8, 'Digital Mixer', 2022, 260000, 4000, 'Самый популярный цифровой пульт в мире.', '32 канала, 25 шин, моторизованные фейдеры', 2, 1);
GO