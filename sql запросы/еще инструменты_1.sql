-- Электрогитары (category_id = 1)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Fender Player Stratocaster', 1, 1, 'Player Series', 2023, 85000, 900, 'Классический страт мексиканской сборки.', 'Ольха, клен, 3 сингла', 1, 5),
('Gibson SG Standard', 2, 1, 'Standard', 2022, 160000, 1800, 'Рок-икона с агрессивным звуком.', 'Махагони, хамбакеры 490R/490T', 2, 2),
('ESP LTD KH-602', 17, 1, 'Kirk Hammett Sig', 2023, 130000, 1500, 'Подписная модель Кирка Хэмметта (Metallica).', 'Сквозной гриф, EMG 81/60, Floyd Rose', 1, 2),
('Jackson Soloist SL2', 19, 1, 'Pro Series', 2022, 110000, 1200, 'Идеально для шреда и скоростной игры.', 'Компаундный радиус, Seymour Duncan', 1, 3),
('PRS SE Custom 24', 20, 1, 'SE Series', 2023, 95000, 1000, 'Универсальная гитара с невероятным внешним видом.', 'Кленовый топ, 24 лада, тремоло PRS', 1, 4),
('Gretsch G5420T Electromatic', 21, 1, 'Hollow Body', 2021, 105000, 1100, 'Полая гитара для рокабилли и джаза.', 'Bigsby тремоло, FilterTron звукосниматели', 2, 1),
('Ibanez RG421', 7, 1, 'RG Series', 2023, 45000, 500, 'Надежная рабочая лошадка для новичка.', 'Фиксированный бридж, тонкий гриф Wizard III', 1, 8),
('Epiphone Casino', 18, 1, 'Archtop', 2022, 75000, 800, 'Классика, на которой играли The Beatles.', 'Полностью полая, датчики P-90', 1, 3),
('Fender Telecaster Vintera 60s', 1, 1, 'Vintera', 2021, 115000, 1300, 'Винтажный звук 60-х в новом исполнении.', 'Ясень, синглы Vintage-Style', 2, 2),
('Gibson Flying V', 2, 1, 'Antique Cherry', 2023, 190000, 2100, 'Экстремальная форма для смелых музыкантов.', 'Махагони, мощные хамбакеры', 1, 1);

-- Акустические гитары (category_id = 2)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Yamaha FG800', 3, 2, 'FG Series', 2023, 35000, 400, 'Самая популярная акустика в мире.', 'Массив ели, нато, фолк-корпус', 1, 10),
('Taylor 214ce-K', 10, 2, '200 Series', 2023, 145000, 1600, 'Гранд Аудиториум с корпусом из коа.', 'Верх из ели, электроника ES2', 1, 3),
('Fender CD-60S', 1, 2, 'Classic Design', 2023, 25000, 300, 'Бюджетная гитара с отличным звуком.', 'Цельная ель, дредноут', 1, 12),
('Gibson J-45 Standard', 2, 2, 'Workhorse', 2022, 280000, 3000, 'Легендарный "джамбо" с богатым низом.', 'Махагони, ель Sitka, LR Baggs VTC', 1, 1),
('Ibanez AW54', 7, 2, 'Artwood', 2023, 32000, 350, 'Теплое звучание цельного махагони.', 'Корпус полностью из махагони', 1, 6),
('Yamaha LL16 ARE', 3, 2, 'L Series', 2022, 95000, 1000, 'Премиальная акустика с технологией старения дерева.', 'Массив палисандра, технология A.R.E.', 2, 2),
('Taylor Academy 10e', 10, 2, 'Academy', 2023, 75000, 800, 'Лучшая гитара для обучения.', 'Эргономичный подлокотник, ель', 1, 4),
('Epiphone DR-100', 18, 2, 'Songmaker', 2023, 18000, 200, 'Идеальный выбор для походов и дачи.', 'Ель, махагони, надежная механика', 1, 15),
('Gretsch G9500 Jim Dandy', 21, 2, 'Roots Collection', 2022, 22000, 250, 'Компактная гитара в стиле 30-х годов.', 'Корпус "парлор", агатис', 1, 5),
('Martin D-28 (Yamaha Equivalent)', 3, 2, 'Custom Shop', 2021, 350000, 4000, 'Инструмент для истинных ценителей.', 'Цельный палисандр, ель, кость', 1, 1);

-- Бас-гитары (category_id = 3)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Fender Jazz Bass Player', 1, 3, 'Player Series', 2023, 90000, 950, 'Гибкий звук для любого жанра.', '2 сингла, ольха, клен', 1, 4),
('Ibanez SR300E', 7, 3, 'SR Series', 2023, 42000, 450, 'Современный бас с активным эквалайзером.', 'PowerSpan датчики, 3-полосный EQ', 1, 7),
('Yamaha TRBX174', 3, 3, 'TRBX', 2023, 24000, 250, 'Отличный первый бас.', 'Конфигурация P/J, махагони', 1, 10),
('Gibson Thunderbird', 2, 3, 'Non-Reverse', 2022, 175000, 1900, 'Мощный рык и уникальный дизайн.', 'Махагони, хамбакеры Ceramic', 2, 1),
('ESP LTD B-204SM', 17, 3, 'B Series', 2023, 65000, 700, 'Красивый топ из капа клена и активный звук.', 'Ясень, топ из клена, 5 струн', 1, 3),
('Squier Affinity Precision Bass', 1, 3, 'Affinity', 2023, 32000, 350, 'Доступный классический бас.', 'Тополь, клен, сплит-сингл', 1, 8),
('Jackson Spectra JS3', 19, 3, 'JS Series', 2022, 38000, 400, 'Современный стиль и мощный выхлоп.', 'Активный темброблок, хамбакеры', 1, 4),
('Warwick RockBass Streamer', 4, 3, 'RockBass', 2023, 72000, 800, 'Немецкое качество сборки.', 'Корпус из каролины, кленовый гриф', 1, 2),
('Ibanez SR1300', 7, 3, 'Premium', 2021, 140000, 1500, 'Профессиональный инструмент серии Premium.', 'Nordstrand Big Single датчики', 3, 1),
('Epiphone EB-3', 18, 3, 'SG Style', 2022, 48000, 500, 'Длинномензурный бас в стиле гитары SG.', 'Махагони, датчик Sidewinder', 1, 3);

-- Ударные (category_id = 4)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Tama Imperialstar', 22, 4, 'IP52H6W', 2023, 95000, 1500, 'Полный комплект с хардвером.', 'Тополь, 5 барабанов, тарелки в комплекте', 1, 2),
('Pearl Roadshow', 5, 4, 'RS525SC', 2023, 65000, 1000, 'Идеально для репетиционных баз.', '9 слоев тополя, стойки в комплекте', 1, 4),
('Yamaha Stage Custom Birch', 3, 4, 'SBP2F5', 2022, 110000, 2000, 'Профессиональный березовый звук.', '100% береза, лаковое покрытие', 2, 2),
('Roland TD-07DMK', 4, 4, 'V-Drums', 2023, 98000, 1400, 'Компактная электронная установка.', 'Сетчатые пэды, модуль TD-07', 1, 3),
('Tama Superstar Classic', 22, 4, 'CK52K', 2023, 135000, 2200, 'Кленовая классика от Tama.', '100% клен, система Star-Mount', 1, 1),
('Pearl Export EXX', 5, 4, 'EXX725', 2023, 82000, 1200, 'Самая продаваемая установка в истории.', 'Тополь/Махагони, Opti-Loc система', 1, 3),
('Yamaha DTX402K', 3, 4, 'Electronic', 2023, 55000, 800, 'Лучшая электронная кухня для дома.', 'Тихие пэды, 10 обучающих программ', 1, 6),
('Zildjian K-Custom Cymbal Set', 23, 4, 'K-Series', 2022, 120000, 1800, 'Набор профессиональных тарелок.', 'Hi-hat 14, Crash 16, Ride 20', 1, 2),
('Tama Woodworks Snare', 22, 4, 'WP1465BK', 2023, 15000, 250, 'Малый барабан с теплым звуком.', 'Тополь, 14x6.5 дюймов', 1, 5),
('Roland V-Drums TD-17KVX', 4, 4, 'V-Drums High', 2022, 185000, 3000, 'Топовая электронная установка для студий.', 'Большой пэд малого барабана, Bluetooth', 2, 1);

-- Клавишные (category_id = 5)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Yamaha P-45', 3, 5, 'Digital Piano', 2023, 52000, 600, 'Самое популярное цифровое пианино.', '88 взвешенных клавиш GHS', 1, 15),
('Casio Privia PX-S1100', 8, 5, 'Privia', 2023, 68000, 800, 'Самое тонкое пианино в мире.', 'Smart Scaled Hammer Action', 1, 8),
('Nord Stage 3 88', 16, 5, 'Stage Series', 2021, 420000, 5000, 'Золотой стандарт для живых концертов.', 'Орган, пианино, синтезатор', 2, 2),
('Korg Minilogue XD', 12, 5, 'Analog Poly', 2022, 75000, 900, 'Гибридный аналоговый синтезатор.', '4 голоса, цифровой мульти-движок', 1, 4),
('Roland FP-30X', 4, 5, 'FP Series', 2023, 82000, 950, 'Мощный звук в компактном корпусе.', 'SuperNATURAL Piano движок, Bluetooth', 1, 6),
('Yamaha Montage 8', 3, 5, 'Flagship', 2021, 450000, 6000, 'Флагманская рабочая станция.', '88 клавиш, синтез Motion Control', 3, 1),
('Korg Kronos 2', 12, 5, 'Workstation', 2022, 380000, 5000, '9 звуковых движков для безграничного творчества.', 'SSD 62ГБ, тачскрин', 2, 1),
('Nord Electro 6D', 16, 5, 'Electro', 2023, 260000, 3500, 'Лучшая эмуляция электромеханических инструментов.', '61 клавиша, полувзвешенная', 1, 2),
('Casio CT-S100', 8, 5, 'Casiotone', 2023, 12000, 150, 'Легкий синтезатор для начинающих.', '61 клавиша, USB to Host', 1, 20),
('Arturia KeyStep (Casio distribution)', 8, 5, 'MIDI', 2023, 14000, 200, 'Компактный контроллер с секвенсором.', '32 клавиши, CV/Gate выходы', 1, 10);

-- Духовые (category_id = 6)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Yamaha YAS-280', 3, 6, 'Alto Sax', 2023, 115000, 1500, 'Лучший студенческий саксофон.', 'Покрытие золотым лаком, высокая F# клавиша', 1, 5),
('Selmer Aristocrat TR600', 6, 6, 'Trumpet', 2022, 55000, 700, 'Надежная труба для оркестра.', 'Латунь, калибр .460', 1, 4),
('Yamaha YFL-222', 3, 6, 'Flute', 2023, 62000, 800, 'Профессиональная студенческая флейта.', 'Никелевое серебро, закрытые клапаны', 1, 6),
('Selmer Prologue', 6, 6, 'Clarinet', 2021, 145000, 1800, 'Кларнет из черного дерева.', 'Гренадиловое дерево, серебряное покрытие', 2, 2),
('Yamaha YTR-4335G', 3, 6, 'Trumpet', 2022, 92000, 1100, 'Труба промежуточного уровня.', 'Золотая латунь, легкий вес', 2, 3),
('Selmer Series II Alto', 6, 6, 'Professional', 2020, 550000, 7000, 'Легенда среди саксофонистов.', 'Ручная гравировка, профессиональная механика', 3, 1),
('Yamaha YSL-354', 3, 6, 'Trombone', 2022, 85000, 1000, 'Популярный тенор-тромбон.', 'Латунь, легкий отклик', 1, 2),
('Pearl Flute PF-505', 5, 6, 'Quantz', 2023, 58000, 750, 'Флейта с отличной интонацией.', 'Механика Pointed Key Arms', 1, 4),
('Hohner Melodica (Yamaha)', 3, 6, 'Student 32', 2023, 6000, 100, 'Мелодика для обучения.', '32 клавиши, мягкий кейс', 1, 15),
('Yamaha YHR-567', 3, 6, 'French Horn', 2021, 320000, 4000, 'Двойная валторна.', 'Золотая латунь, надежные роторы', 2, 1);

-- Микрофоны (category_id = 7)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Shure SM7B', 9, 7, 'Broadcast', 2023, 45000, 600, 'Стандарт для подкастов и вокала.', 'Динамический, кардиоида, защита от помех', 1, 8),
('Neumann TLM 103', 13, 7, 'Studio', 2022, 135000, 1800, 'Профессиональный студийный микрофон.', 'Конденсаторный, большой капсюль', 1, 3),
('Sennheiser e945', 14, 7, 'Live Vocal', 2023, 22000, 300, 'Лучший выбор для живой сцены.', 'Суперкардиоида, высокая устойчивость к фидбэку', 1, 12),
('Shure Beta 58A', 9, 7, 'Vocal', 2023, 18000, 250, 'Улучшенная версия классического SM58.', 'Суперкардиоида, неодимовый магнит', 1, 15),
('Sennheiser MK 4', 14, 7, 'Studio', 2022, 35000, 450, 'Универсальный студийный конденсаторник.', 'Сделано в Германии, 1-дюймовый капсюль', 1, 5),
('Neumann U87 Ai', 13, 7, 'Legendary', 2021, 380000, 5000, 'Микрофон, который есть в каждой топовой студии.', '3 диаграммы направленности, НЧ-фильтр', 2, 1),
('Shure SM57', 9, 7, 'Instrument', 2023, 11000, 150, 'Микрофон для малого барабана и гитарных кабинетов.', 'Динамический, выдерживает высокое давление', 1, 20),
('Sennheiser e604', 14, 7, 'Drum Mic', 2023, 14000, 200, 'Компактный микрофон для томов.', 'Крепление на обод в комплекте', 1, 10),
('AKG C414 (Sennheiser equivalent)', 14, 7, 'XLII', 2021, 110000, 1400, 'Микрофон с 9 диаграммами направленности.', 'Конденсаторный, эталонный звук', 2, 2),
('Rode NT1 (Shure distribution)', 9, 7, 'Gen 5', 2023, 28000, 350, 'Самый тихий микрофон в мире.', '32-bit float выход, USB/XLR', 1, 6);

-- Усилители (category_id = 8)
INSERT INTO instruments (name, brand_id, category_id, model, year_of_manufacture, purchase_price, rental_price_per_day, description, characteristics, condition_id, quantity_in_stock) VALUES
('Marshall DSL40CR', 11, 8, 'Combo', 2023, 95000, 1200, 'Ламповый комбо с легендарным британским звуком.', '40 Вт, 12" динамик Celestion', 1, 3),
('Orange Crush 35RT', 15, 8, 'Crush Series', 2023, 28000, 350, 'Транзисторный комбо с отличным перегрузом.', '35 Вт, тюнер, ревербератор', 1, 6),
('Fender Mustang GTX100', 1, 8, 'Modeling', 2022, 55000, 700, 'Цифровой моделирующий усилитель.', '100 Вт, WiFi, Bluetooth, 200 пресетов', 1, 4),
('Marshall JVM410H', 11, 8, 'Head', 2021, 185000, 2200, 'Флагманская "голова" Marshall.', '100 Вт, 4 канала, 12 режимов', 2, 1),
('Orange Rockerverb 50 MKIII', 15, 8, 'Combo', 2022, 210000, 2500, 'Профессиональный ламповый комбо.', '50 Вт, встроенный аттенюатор', 1, 2),
('Fender Blues Junior IV', 1, 8, 'Blues', 2023, 82000, 1000, 'Компактная классика для блюза и рока.', '15 Вт, лампы EL84, пружинный ревер', 1, 4),
('Boss Katana-50 MkII (Roland)', 4, 8, 'Modeling', 2023, 35000, 450, 'Самый популярный домашний усилитель.', '50 Вт, 5 типов усиления, 60+ эффектов', 1, 10),
('Yamaha THR10II', 3, 8, 'Desktop', 2023, 38000, 450, 'Лучший усилитель для стола.', 'Беспроводной, Hi-Fi звук', 1, 7),
('Orange Micro Dark', 15, 8, 'Hybrid', 2023, 22000, 250, 'Крошечная голова с огромным звуком.', '20 Вт, гибридная схема (лампа в преампе)', 1, 5),
('Marshall CODE50', 11, 8, 'Digital', 2022, 32000, 400, 'Полная эмуляция классических стеков Marshall.', '50 Вт, управление со смартфона', 1, 5),
('Peavey 6505 (ESP equivalent)', 17, 8, 'Metal Head', 2021, 140000, 1700, 'Стандарт тяжелого металла.', '120 Вт, лампы 6L6GC', 3, 1),
('Focusrite Scarlett 2i2', 25, 8, 'Audio Interface', 2023, 22000, 250, 'Самая популярная звуковая карта.', '2 входа, 2 выхода, Air mode', 1, 20),
('Focusrite Scarlett Solo', 25, 8, 'Audio Interface', 2023, 14000, 150, 'Идеально для записи гитары и вокала.', '1 вход, 1 выход, 4th Gen', 1, 15),
('Behringer UM2', 24, 8, 'Budget Interface', 2023, 6000, 100, 'Самый бюджетный аудиоинтерфейс.', '48 кГц, фантомное питание', 1, 30),
('Behringer UMC404HD', 24, 8, 'U-Phoria', 2023, 18000, 250, 'Профессиональная запись за копейки.', '4 входа Midas, 192 кГц', 1, 10);
GO