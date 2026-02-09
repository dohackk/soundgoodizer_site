from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import pyodbc
import hashlib
from functools import wraps
from collections import namedtuple
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
import os
import dns.resolver

app = Flask(__name__)
app.secret_key = 'soundgoodizer-secret-key-2025-super-secure'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'e.saltymakov06@gmail.com'
app.config['MAIL_PASSWORD'] = 'vbfm gowd elnj nxjg'
app.config['MAIL_DEFAULT_SENDER'] = 'e.saltymakov06@gmail.com'

mail = Mail(app)

def get_db_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=DESKTOP-L694H77;'
            'DATABASE=soundgoodizerBD;'
            'Trusted_Connection=yes;'
            'TrustServerCertificate=yes;'
        )
        return conn
    except Exception as e:
        print(f"ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Сначала войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('Доступ запрещен. Требуются права администратора', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_instruments(where_clause="", params=()):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        sql = f"""
        SELECT 
            i.instrument_id,
            i.name,
            i.model,
            i.year_of_manufacture,
            i.purchase_price,
            i.rental_price_per_day,
            i.rental_price_per_week,
            i.rental_price_per_month,
            i.description,
            i.characteristics,
            i.condition_id,
            i.quantity_in_stock,
            i.is_available_for_sale,
            i.is_available_for_rent,
            i.main_image_url,
            i.created_by,
            i.created_at,
            i.views_count,
            b.brand_name,
            c.category_name,
            ic.condition_name,
            i.brand_id,
            i.category_id
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN instrument_conditions ic ON i.condition_id = ic.condition_id
        {where_clause}
        ORDER BY i.name
        """
        
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        
        Instrument = namedtuple('Instrument', columns)
        instruments = [Instrument(*row) for row in cursor.fetchall()]
        
        conn.close()
        return instruments
        
    except Exception as e:
        print(f"Ошибка при получении инструментов: {e}")
        conn.close()
        return []

def send_verification_email(email, verification_code):
    """Отправка email с кодом подтверждения"""
    try:
        msg = Message(
            subject='Подтверждение email - SoundGoodizer',
            recipients=[email]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .code {{ font-size: 32px; font-weight: bold; color: #667eea; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SoundGoodizer</h1>
                    <p>Подтверждение email адреса</p>
                </div>
                
                <p>Здравствуйте!</p>
                <p>Благодарим вас за регистрацию в SoundGoodizer. Для завершения регистрации необходимо подтвердить ваш email адрес.</p>
                
                <p>Ваш код подтверждения:</p>
                <div class="code">{verification_code}</div>
                
                <p>Введите этот 6-значный код на странице подтверждения на сайте SoundGoodizer.</p>
                
                <p><strong>Код действителен 24 часа.</strong></p>
                
                <p>Если вы не регистрировались на SoundGoodizer, просто проигнорируйте это письмо.</p>
                
                <hr>
                
                <p style="color: #666; font-size: 12px;">
                    © SoundGoodizer. Все права защищены.<br>
                    Это письмо отправлено автоматически, пожалуйста, не отвечайте на него.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.body = f"""
        Здравствуйте!
        
        Благодарим вас за регистрацию в SoundGoodizer.
        
        Ваш код подтверждения: {verification_code}
        
        Введите этот 6-значный код на странице подтверждения на сайте SoundGoodizer.
        
        Код действителен 24 часа.
        
        Если вы не регистрировались на SoundGoodizer, просто проигнорируйте это письмо.
        
        © SoundGoodizer
        """
        
        mail.send(msg)
        print(f"✓ Email с кодом подтверждения отправлен на {email}")
        return True
    except Exception as e:
        print(f"✗ Ошибка отправки email: {e}")
        return False

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="Ошибка подключения к базе данных")
    
    cursor = conn.cursor()
    
    try:
        sql = """
        SELECT TOP 8 
            i.instrument_id,
            i.name,
            i.model,
            i.description,
            b.brand_name,
            i.purchase_price,
            i.rental_price_per_day,
            i.quantity_in_stock,
            i.is_available_for_sale,
            i.main_image_url,
            i.brand_id,
            i.category_id,
            i.condition_id,
            i.is_available_for_rent,
            i.created_by,
            i.created_at,
            i.views_count,
            c.category_name,
            CASE 
                WHEN i.main_image_url IS NOT NULL AND i.main_image_url != '' 
                THEN i.main_image_url
                ELSE 'img/default-instrument.jpg'
            END as image_path
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        LEFT JOIN categories c ON i.category_id = c.category_id
        WHERE i.is_available_for_sale = 1
        ORDER BY i.views_count DESC, i.instrument_id DESC
        """
        cursor.execute(sql)
        instruments = cursor.fetchall()
        
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        
        conn.close()
        
        return render_template('index.html', 
                             instruments=instruments, 
                             categories=categories)
    except Exception as e:
        conn.close()
        return render_template('error.html', error=f"Ошибка при загрузке данных: {str(e)}")

@app.route('/catalog')
def catalog():
    category_id = request.args.get('category_id')
    search = request.args.get('search', '')
    brand_id = request.args.get('brand_id')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    where_conditions = ["i.is_available_for_sale = 1"]
    params = []
    
    if search:
        where_conditions.append("(i.name LIKE ? OR i.description LIKE ? OR i.model LIKE ?)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if category_id:
        where_conditions.append("i.category_id = ?")
        params.append(category_id)
    
    if brand_id:
        where_conditions.append("i.brand_id = ?")
        params.append(brand_id)
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="Ошибка подключения к базе данных")
    
    cursor = conn.cursor()
    
    count_sql = f"SELECT COUNT(*) FROM instruments i {where_clause}"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]
    
    offset = (page - 1) * per_page
    
    sql = f"""
    SELECT 
        i.instrument_id,
        i.name,
        i.model,
        i.year_of_manufacture,
        i.purchase_price,
        i.rental_price_per_day,
        i.rental_price_per_week,
        i.rental_price_per_month,
        i.description,
        i.characteristics,
        i.condition_id,
        i.quantity_in_stock,
        i.is_available_for_sale,
        i.is_available_for_rent,
        i.main_image_url,
        i.created_by,
        i.created_at,
        i.views_count,
        b.brand_name,
        c.category_name,
        ic.condition_name,
        i.brand_id,
        i.category_id
    FROM instruments i
    LEFT JOIN brands b ON i.brand_id = b.brand_id
    LEFT JOIN categories c ON i.category_id = c.category_id
    LEFT JOIN instrument_conditions ic ON i.condition_id = ic.condition_id
    {where_clause}
    ORDER BY i.name
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    
    pagination_params = params + [offset, per_page]
    cursor.execute(sql, pagination_params)
    
    columns = [column[0] for column in cursor.description]
    Instrument = namedtuple('Instrument', columns)
    instruments = [Instrument(*row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM categories ORDER BY category_name")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM brands ORDER BY brand_name")
    brands = cursor.fetchall()
    
    conn.close()
    
    total_pages = (total_count + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None,
        'iter_pages': range(max(1, page - 2), min(total_pages, page + 2) + 1)
    }
    
    return render_template('catalog.html',
                         instruments=instruments,
                         categories=categories,
                         brands=brands,
                         search_term=search,
                         selected_category=category_id,
                         selected_brand=brand_id,
                         pagination=pagination)

@app.route('/instrument/<int:instrument_id>')
def instrument_detail(instrument_id):
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="Ошибка подключения к базе данных")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE instruments SET views_count = views_count + 1 WHERE instrument_id = ?", 
                      (instrument_id,))
        conn.commit()
        
        sql = """
        SELECT 
            i.instrument_id,
            i.name,
            i.model,
            i.year_of_manufacture,
            i.purchase_price,
            i.rental_price_per_day,
            i.rental_price_per_week,
            i.rental_price_per_month,
            i.description,
            i.characteristics,
            i.condition_id,
            i.quantity_in_stock,
            i.is_available_for_sale,
            i.is_available_for_rent,
            i.main_image_url,
            i.created_by,
            i.created_at,
            i.views_count,
            b.brand_name,
            c.category_name,
            ic.condition_name,
            i.brand_id,
            i.category_id
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN instrument_conditions ic ON i.condition_id = ic.condition_id
        WHERE i.instrument_id = ?
        """
        cursor.execute(sql, (instrument_id,))
        instrument = cursor.fetchone()
        
        if not instrument:
            conn.close()
            flash('Инструмент не найден', 'danger')
            return redirect(url_for('catalog'))
        
        similar_sql = """
        SELECT TOP 4 
            i.instrument_id,
            i.name,
            i.model,
            i.purchase_price,
            i.rental_price_per_day,
            i.quantity_in_stock,
            i.main_image_url,
            i.views_count,
            b.brand_name,
            c.category_name,
            CASE 
                WHEN i.main_image_url IS NOT NULL AND i.main_image_url != '' 
                THEN i.main_image_url
                ELSE 'img/default-instrument.jpg'
            END as image_path
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        LEFT JOIN categories c ON i.category_id = c.category_id
        WHERE i.category_id = ? 
        AND i.instrument_id != ? 
        AND i.is_available_for_sale = 1 
        ORDER BY NEWID()
        """
        cursor.execute(similar_sql, (instrument[22], instrument_id))
        similar = cursor.fetchall()
        
        conn.close()
        
        return render_template('instrument.html', 
                             instrument=instrument, 
                             similar=similar)
    except Exception as e:
        conn.close()
        return render_template('error.html', error=f"Ошибка при загрузке инструмента: {str(e)}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Заполните все поля', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Ошибка подключения к базе данных', 'danger')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor()
            
            sql = """
            SELECT u.*, r.role_name, u.avatar_url
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.login = ? AND u.is_active = 1
            """
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            
            if user:
                stored_password_hash = user[3]
                input_password_hash = hash_password(password)
                
                if stored_password_hash == input_password_hash:
                    is_email_verified = user[12]
                    
                    if not is_email_verified:
                        session['pending_verification_email'] = user[2]
                        session['pending_user_id'] = user[0]
                        
                        verification_code = secrets.randbelow(900000) + 100000
                        code_str = str(verification_code)
                        expires_at = datetime.now() + timedelta(hours=24)
                        
                        cursor.execute("""
                        UPDATE users 
                        SET email_verification_code = ?, email_verification_expires = ?
                        WHERE user_id = ?
                        """, (code_str, expires_at, user[0]))
                        conn.commit()
                        
                        send_verification_email(user[2], code_str)
                        
                        flash('Сначала подтвердите ваш email. Код отправлен на вашу почту.', 'warning')
                        conn.close()
                        return redirect(url_for('verify_email'))
                    
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['user_name'] = f"{user[4]} {user[5]}"
                    session['user_role'] = user[18]
                    session['user_email'] = user[2]
                    session['user_avatar'] = user[11]
                    session['is_email_verified'] = True

                    flash(f'Добро пожаловать, {session["user_name"]}!', 'success')
                    conn.close()
                    return redirect(url_for('index'))
                else:
                    flash('Неверный пароль', 'danger')
            else:
                flash('Пользователь не найден', 'danger')
            
            conn.close()
        except Exception as e:
            conn.close()
            flash(f'Ошибка при входе: {str(e)}', 'danger')
    
    return render_template('login.html')

@app.route('/api/check-unique', methods=['POST'])
def api_check_unique():
    """API: проверка уникальности поля"""
    data = request.get_json()
    field = data.get('field')
    value = data.get('value', '').strip()
    
    if not field or not value:
        return jsonify({'exists': False})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'exists': False})
    
    try:
        cursor = conn.cursor()
        
        if field == 'phone':
            digits = ''.join(filter(str.isdigit, value))
            if digits.startswith('7') or digits.startswith('8'):
                digits = digits[1:]
            
            cursor.execute("""
                SELECT phone FROM users 
                WHERE phone IS NOT NULL AND phone != ''
            """)
            all_phones = cursor.fetchall()
            
            exists = False
            for phone_record in all_phones:
                if phone_record[0]:
                    phone_digits = ''.join(filter(str.isdigit, phone_record[0]))
                    if phone_digits.startswith('7') or phone_digits.startswith('8'):
                        phone_digits = phone_digits[1:]
                    
                    if phone_digits == digits:
                        exists = True
                        break
            
            conn.close()
            return jsonify({'exists': exists})
        
        else:
            if field == 'login':
                cursor.execute("SELECT login FROM users WHERE login = ?", (value,))
            elif field == 'email':
                cursor.execute("SELECT email FROM users WHERE email = ?", (value,))
            else:
                conn.close()
                return jsonify({'exists': False})
            
            result = cursor.fetchone()
            conn.close()
            return jsonify({'exists': result is not None})
            
    except Exception as e:
        conn.close()
        print(f"Ошибка при проверке уникальности: {e}")
        return jsonify({'exists': False})

@app.route('/api/check-email-dns', methods=['POST'])
def api_check_email_dns():
    """API: проверка email через DNS"""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'valid': False, 'message': 'Некорректный формат email'})
    
    try:
        domain = email.split('@')[1]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if len(mx_records) == 0:
                return jsonify({'valid': False, 'message': 'Доменное имя почты не настроено для приема почты'})
        except dns.resolver.NoAnswer:
            return jsonify({'valid': False, 'message': 'Доменное имя почты не настроено для приема почты'})
        except dns.resolver.NXDOMAIN:
            return jsonify({'valid': False, 'message': 'Доменное имя почты не существует'})
        except dns.resolver.NoNameservers:
            try:
                dns.resolver.resolve(domain, 'A')
            except:
                return jsonify({'valid': False, 'message': 'Не удалось проверить существование домена почты'})
        except Exception as e:
            print(f"DNS проверка пропущена: {e}")
            return jsonify({'valid': True, 'message': ''})
        
        return jsonify({'valid': True, 'message': ''})
        
    except Exception as e:
        print(f"Ошибка при проверке email DNS: {e}")
        return jsonify({'valid': True, 'message': ''})
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        form_data = {
            'login': login,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone
        }
        
        errors = []
        if not login or len(login) < 3:
            errors.append('Логин должен содержать минимум 3 символа')
        if not email or '@' not in email:
            errors.append('Введите корректный email')
        if not password or len(password) < 6:
            errors.append('Пароль должен содержать минимум 6 символов')
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        if not first_name:
            errors.append('Введите имя')
        if not last_name:
            errors.append('Введите фамилию')

        if not phone:
            errors.append('Введите номер телефона')
        else:
            digits = ''.join(filter(str.isdigit, phone))
            
            if digits.startswith('7') or digits.startswith('8'):
                digits = digits[1:]
            
            if len(digits) != 10:
                errors.append('Номер телефона должен содержать 10 цифр')
            else:
                phone = f"+7 ({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
                form_data['phone'] = phone
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', **form_data)
        
        conn = get_db_connection()
        if not conn:
            flash('Ошибка подключения к базе данных', 'danger')
            return render_template('register.html', **form_data)
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT login, email, phone 
                FROM users 
                WHERE login = ? OR email = ?
            """, (login, email))
            
            existing_users = cursor.fetchall()
            
            duplicate_errors = []
            for user in existing_users:
                if user[0] == login:
                    duplicate_errors.append('Такой логин уже существует')
                if user[1] == email:
                    duplicate_errors.append('Такой email уже зарегистрирован')
            
            phone_digits = ''.join(filter(str.isdigit, phone))
            if phone_digits.startswith('7') or phone_digits.startswith('8'):
                phone_digits = phone_digits[1:]
            
            cursor.execute("SELECT phone FROM users WHERE phone IS NOT NULL AND phone != ''")
            all_phones = cursor.fetchall()
            
            for phone_record in all_phones:
                if phone_record[0]:
                    user_phone_digits = ''.join(filter(str.isdigit, phone_record[0]))
                    if user_phone_digits.startswith('7') or user_phone_digits.startswith('8'):
                        user_phone_digits = user_phone_digits[1:]
                    
                    if user_phone_digits == phone_digits:
                        duplicate_errors.append('Такой номер телефона уже зарегистрирован')
                        break
            
            if duplicate_errors:
                for error in duplicate_errors:
                    flash(error, 'danger')
                conn.close()
                return render_template('register.html', **form_data)
            
            verification_code = secrets.randbelow(900000) + 100000
            verification_code_str = str(verification_code)
            expires_at = datetime.now() + timedelta(hours=24)
            
            password_hash = hash_password(password)
            
            sql = """
            INSERT INTO users (login, email, password_hash, first_name, last_name, 
                             phone, role_id, is_active, is_email_verified,
                             email_verification_code, email_verification_expires)
            VALUES (?, ?, ?, ?, ?, ?, 4, 1, 0, ?, ?)
            """
            cursor.execute(sql, (login, email, password_hash, first_name, last_name, phone,
                               verification_code_str, expires_at))
            conn.commit()
            
            cursor.execute("SELECT @@IDENTITY")
            user_id = cursor.fetchone()[0]
            
            conn.close()
            
            email_sent = send_verification_email(email, verification_code_str)
            
            if email_sent:
                flash(f'Регистрация успешна! Код подтверждения отправлен на {email}', 'success')
                session['pending_verification_email'] = email
                session['pending_user_id'] = user_id
                return redirect(url_for('verify_email'))
            else:
                flash('Регистрация успешна, но не удалось отправить email. Обратитесь к администратору.', 'warning')
                return redirect(url_for('verify_email'))
            
        except Exception as e:
            conn.close()
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            return render_template('register.html', **form_data)
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Страница подтверждения email"""
    email = session.get('pending_verification_email')
    user_id = session.get('pending_user_id')
    
    if not email or not user_id:
        flash('Сначала зарегистрируйтесь', 'warning')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        
        if not code or len(code) != 6:
            flash('Введите 6-значный код подтверждения', 'danger')
            return render_template('verify_email.html', email=email)
        
        conn = get_db_connection()
        if not conn:
            flash('Ошибка подключения к базе данных', 'danger')
            return render_template('verify_email.html', email=email)
        
        try:
            cursor = conn.cursor()
            
            sql = """
            SELECT email_verification_code, email_verification_expires 
            FROM users 
            WHERE user_id = ? AND email = ? AND is_email_verified = 0
            """
            cursor.execute(sql, (user_id, email))
            result = cursor.fetchone()
            
            if result:
                stored_code, expires_at = result
                
                if not stored_code:
                    flash('Код подтверждения не найден', 'danger')
                elif expires_at and expires_at < datetime.now():
                    flash('Срок действия кода истек. Запросите новый код.', 'danger')
                elif stored_code == code:
                    cursor.execute("""
                    UPDATE users 
                    SET is_email_verified = 1, 
                        email_verification_code = NULL,
                        email_verification_expires = NULL
                    WHERE user_id = ?
                    """, (user_id,))
                    conn.commit()
                    
                    cursor.execute("""
                    SELECT u.*, r.role_name, u.avatar_url
                    FROM users u
                    JOIN roles r ON u.role_id = r.role_id
                    WHERE u.user_id = ?
                    """, (user_id,))
                    user = cursor.fetchone()
                    
                    session.pop('pending_verification_email', None)
                    session.pop('pending_user_id', None)
                    
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['user_name'] = f"{user[4]} {user[5]}"
                    session['user_role'] = user[18]
                    session['user_email'] = user[2]
                    session['user_avatar'] = user[11]
                    session['is_email_verified'] = True
                    
                    conn.close()
                    
                    flash('Email успешно подтвержден! Добро пожаловать в SoundGoodizer!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Неверный код подтверждения', 'danger')
            else:
                flash('Пользователь не найден или email уже подтвержден', 'danger')
            
            conn.close()
        except Exception as e:
            conn.close()
            flash(f'Ошибка при подтверждении email: {str(e)}', 'danger')
    
    return render_template('verify_email.html', email=email)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Повторная отправка кода подтверждения"""
    email = session.get('pending_verification_email')
    user_id = session.get('pending_user_id')
    
    if not email or not user_id:
        return jsonify({'success': False, 'message': 'Сессия истекла. Зарегистрируйтесь заново.'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Ошибка подключения к БД'})
    
    try:
        cursor = conn.cursor()
        
        new_code = secrets.randbelow(900000) + 100000
        new_code_str = str(new_code)
        new_expires = datetime.now() + timedelta(hours=24)
        
        cursor.execute("""
        UPDATE users 
        SET email_verification_code = ?, email_verification_expires = ?
        WHERE user_id = ? AND email = ? AND is_email_verified = 0
        """, (new_code_str, new_expires, user_id, email))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Пользователь не найден или email уже подтвержден'})
        
        conn.commit()
        
        email_sent = send_verification_email(email, new_code_str)
        
        conn.close()
        
        if email_sent:
            return jsonify({'success': True, 'message': 'Новый код отправлен на email'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка отправки email'})
            
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT avatar_url, password_hash FROM users WHERE user_id = ?", (session['user_id'],))
        current_data = cursor.fetchone()
        current_avatar_path = current_data[0] if current_data and current_data[0] else None
        current_password_hash = current_data[1] if current_data else None
        
        if request.method == 'POST':
            import os
            import uuid
            
            if request.form.get('delete_avatar'):
                if current_avatar_path:
                    file_path = os.path.join('static', current_avatar_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                cursor.execute(
                    "UPDATE users SET avatar_url = NULL WHERE user_id = ?",
                    (session['user_id'],)
                )
                conn.commit()
                session['user_avatar'] = None
                
                flash('Фото профиля удалено', 'info')
                return redirect(url_for('profile'))
            
            if 'avatar' in request.files:
                file = request.files['avatar']
                
                if file.filename != '':
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('Разрешены только файлы: PNG, JPG, JPEG, GIF, WEBP', 'danger')
                    else:
                        if current_avatar_path:
                            old_file_path = os.path.join('static', current_avatar_path)
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)
                        
                        username = session['username']
                        safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).lower()
                        
                        filename = f"{safe_username}_{uuid.uuid4().hex[:8]}.{file_ext}"
                        upload_folder = 'static/uploads/avatars'
                        
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        
                        avatar_url = f'uploads/avatars/{filename}'
                        
                        cursor.execute(
                            "UPDATE users SET avatar_url = ? WHERE user_id = ?",
                            (avatar_url, session['user_id'])
                        )
                        conn.commit()
                        
                        session['user_avatar'] = avatar_url
                        
                        flash('Фото профиля успешно обновлено!', 'success')
                        return redirect(url_for('profile'))
                else:
                    flash('Файл не выбран', 'warning')
            
            if request.form.get('change_password'):
                current_password = request.form.get('current_password', '').strip()
                new_password = request.form.get('new_password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()
                
                if not current_password or not new_password or not confirm_password:
                    flash('Заполните все поля', 'danger')
                elif new_password != confirm_password:
                    flash('Новые пароли не совпадают', 'danger')
                elif len(new_password) < 6:
                    flash('Новый пароль должен содержать минимум 6 символов', 'danger')
                else:
                    current_password_hash_input = hashlib.sha256(current_password.encode()).hexdigest()
                    
                    if current_password_hash_input != current_password_hash:
                        flash('Текущий пароль неверен', 'danger')
                    else:
                        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                        
                        cursor.execute(
                            "UPDATE users SET password_hash = ? WHERE user_id = ?",
                            (new_password_hash, session['user_id'])
                        )
                        conn.commit()
                        
                        flash('Пароль успешно изменен!', 'success')
                        return redirect(url_for('profile'))
        
        cursor.execute("""
            SELECT u.*, r.role_name 
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = ?
        """, (session['user_id'],))
        user = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) FROM cart_items WHERE user_id = ?
        """, (session['user_id'],))
        cart_items = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM purchase_orders WHERE user_id = ?
        """, (session['user_id'],))
        orders_count = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM rental_orders WHERE user_id = ?
        """, (session['user_id'],))
        rentals_count = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT TOP 5 po.*, os.status_name 
            FROM purchase_orders po
            JOIN order_statuses os ON po.status_id = os.status_id
            WHERE po.user_id = ?
            ORDER BY po.order_date DESC
        """, (session['user_id'],))
        recent_orders = cursor.fetchall()
        
        conn.close()
        
        return render_template('profile.html',
                             user=user,
                             cart_items=cart_items,
                             orders_count=orders_count,
                             rentals_count=rentals_count,
                             recent_orders=recent_orders)
        
    except Exception as e:
        conn.close()
        flash(f'Ошибка при загрузке профиля: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    """Корзина пользователя"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT ci.*, i.name, i.purchase_price, i.main_image_url, i.quantity_in_stock
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.user_id = ?
        """
        cursor.execute(sql, (session['user_id'],))
        cart_items = cursor.fetchall()
        
        total = 0
        items_list = []
        for item in cart_items:
            item_total = item[2] * item[3]
            total += item_total
            items_list.append({
                'id': item[0],
                'instrument_id': item[2],
                'name': item[7],
                'price': item[8],
                'quantity': item[3],
                'image': item[9],
                'stock': item[10],
                'total': item_total
            })
        
        conn.close()
        
        return render_template('cart.html', cart_items=items_list, total=total)
    except Exception as e:
        conn.close()
        flash(f'Ошибка при загрузке корзины: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
@app.route('/add_to_cart/<int:instrument_id>')
@login_required
def add_to_cart(instrument_id):
    """Добавление товара в корзину"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(request.referrer or url_for('catalog'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantity_in_stock FROM instruments WHERE instrument_id = ?", 
                      (instrument_id,))
        stock = cursor.fetchone()
        
        if not stock or stock[0] <= 0:
            flash('Товар отсутствует в наличии', 'warning')
            conn.close()
            return redirect(request.referrer or url_for('catalog'))
        
        sql = "SELECT cart_item_id, quantity FROM cart_items WHERE user_id = ? AND instrument_id = ?"
        cursor.execute(sql, (session['user_id'], instrument_id))
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing[1] + 1
            if new_quantity <= stock[0]:
                cursor.execute("UPDATE cart_items SET quantity = ? WHERE cart_item_id = ?",
                             (new_quantity, existing[0]))
                flash('Товар добавлен в корзину', 'success')
            else:
                flash('Недостаточно товара на складе', 'warning')
        else:
            cursor.execute("""
                INSERT INTO cart_items (user_id, instrument_id, quantity, is_for_rental)
                VALUES (?, ?, 1, 0)
            """, (session['user_id'], instrument_id))
            flash('Товар добавлен в корзину', 'success')
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        conn.close()
        flash(f'Ошибка при добавлении в корзину: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('catalog'))

@app.route('/remove_from_cart/<int:cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    """Удаление товара из корзины"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('cart'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart_items WHERE cart_item_id = ? AND user_id = ?",
                      (cart_item_id, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Товар удален из корзины', 'info')
    except Exception as e:
        conn.close()
        flash(f'Ошибка при удалении из корзины: {str(e)}', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Административная панель"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM instruments")
        stats['instruments'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM purchase_orders")
        stats['orders'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rental_orders")
        stats['rentals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM repair_requests")
        stats['repairs'] = cursor.fetchone()[0]
        
        sql = """
        SELECT TOP 10 po.*, u.login, os.status_name 
        FROM purchase_orders po
        JOIN users u ON po.user_id = u.user_id
        JOIN order_statuses os ON po.status_id = os.status_id
        ORDER BY po.order_date DESC
        """
        cursor.execute(sql)
        recent_orders = cursor.fetchall()
        
        sql = "SELECT TOP 5 * FROM users ORDER BY created_at DESC"
        cursor.execute(sql)
        recent_users = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_orders=recent_orders,
                             recent_users=recent_users)
    except Exception as e:
        conn.close()
        flash(f'Ошибка при загрузке админ-панели: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/instruments')
@login_required
@admin_required
def admin_instruments():
    """Управление инструментами"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT 
            i.instrument_id,
            i.name,
            i.model,
            i.year_of_manufacture,
            i.purchase_price,
            i.rental_price_per_day,
            i.quantity_in_stock,
            i.is_available_for_sale,
            i.main_image_url,
            b.brand_name,
            c.category_name,
            ic.condition_name,
            i.views_count,
            i.created_at
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN instrument_conditions ic ON i.condition_id = ic.condition_id
        ORDER BY i.instrument_id DESC
        """
        cursor.execute(sql)
        instruments = cursor.fetchall()
        
        cursor.execute("SELECT * FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        
        cursor.execute("SELECT * FROM brands ORDER BY brand_name")
        brands = cursor.fetchall()

        cursor.execute("SELECT * FROM instrument_conditions ORDER BY condition_name")
        conditions = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/instruments.html',
                             instruments=instruments,
                             categories=categories,
                             brands=brands,
                             conditions=conditions)
    except Exception as e:
        conn.close()
        flash(f'Ошибка при загрузке инструментов: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/cart_count')
def api_cart_count():
    """API: количество товаров в корзине"""
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'count': 0})
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(quantity) FROM cart_items WHERE user_id = ?", 
                      (session['user_id'],))
        result = cursor.fetchone()
        count = result[0] if result[0] else 0
        conn.close()
        return jsonify({'count': count})
    except:
        conn.close()
        return jsonify({'count': 0})

@app.route('/api/categories')
def api_categories():
    """API: все категории"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        conn.close()
        
        result = [{'id': c[0], 'name': c[1]} for c in categories]
        return jsonify(result)
    except:
        conn.close()
        return jsonify([])

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Страница не найдена'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error='Внутренняя ошибка сервера'), 500

if __name__ == '__main__':
    print("=" * 50)
    print("ЗАПУСК SOUNDGOODIZER")
    print("=" * 50)
    
    conn = get_db_connection()
    if conn:
        print("✅ Подключение к базе данных УСПЕШНО")
        
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM instruments")
            count = cursor.fetchone()[0]
            print(f"✅ В базе данных найдено {count} инструментов")
        except:
            print("⚠️  Таблица instruments не найдена")
        
        conn.close()
    else:
        print("❌ ОШИБКА: Не удалось подключиться к базе данных")
    
    print("=" * 50)
    print("Сервер запускается на http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)