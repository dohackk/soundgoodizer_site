from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import psycopg2.extras
import psycopg2.pool
import hashlib
from functools import wraps
from collections import namedtuple
from flask_mail import Mail, Message
import secrets
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import dns.resolver
import random
import uuid
from urllib.parse import urlparse


UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

REPAIR_PHOTOS_FOLDER = 'static/uploads/repair_photos'
ALLOWED_REPAIR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

INSTRUMENT_IMAGES_FOLDER = 'static/img/instruments'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPAIR_PHOTOS_FOLDER'] = REPAIR_PHOTOS_FOLDER
app.config['INSTRUMENT_IMAGES_FOLDER'] = INSTRUMENT_IMAGES_FOLDER

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

_db_pool = None

def get_db_pool():
    global _db_pool
    if _db_pool is not None:
        return _db_pool

    database_url = os.environ.get('DATABASE_URL')
    try:
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            result = urlparse(database_url)
            _db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1, maxconn=10,
                host=result.hostname,
                port=result.port or 5432,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                sslmode='require',
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
        else:
            _db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1, maxconn=10,
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 5432)),
                database=os.environ.get('DB_NAME', 'soundgoodizerBD'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', '')
            )
    except Exception as e:
        print(f"ОШИБКА СОЗДАНИЯ ПУЛА СОЕДИНЕНИЙ: {e}")
        _db_pool = None

    return _db_pool

def get_db_connection():
    pool = get_db_pool()
    if not pool:
        return None
    try:
        conn = pool.getconn()
        # Проверяем что соединение живое
        if conn.closed:
            pool.putconn(conn)
            global _db_pool
            _db_pool = None
            pool = get_db_pool()
            conn = pool.getconn()
        try:
            conn.cursor().execute('SELECT 1')
        except Exception:
            pool.putconn(conn)
            _db_pool = None
            pool = get_db_pool()
            conn = pool.getconn()
        return conn
    except Exception as e:
        print(f"ОШИБКА ПОЛУЧЕНИЯ СОЕДИНЕНИЯ ИЗ ПУЛА: {e}")
        return None

def release_conn(conn):
    if conn is None:
        return
    pool = get_db_pool()
    if pool:
        try:
            pool.putconn(conn)
        except Exception:
            try:
                release_conn(conn)
            except Exception:
                pass
    else:
        try:
            release_conn(conn)
        except Exception:
            pass

def generate_order_number():
    """Генерирует уникальный номер заказа"""
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = random.randint(10000, 99999)
    return f"ORD-{date_part}-{random_part}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Сначала войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def technician_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Сначала войдите в систему', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') not in ['admin', 'technician']:
            flash('Доступ запрещен. Требуются права мастера или администратора', 'danger')
            return redirect(url_for('index'))
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_avatar(file, login):
    if not allowed_file(file.filename):
        return None
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{login}.{extension}"
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    delete_old_avatar(login)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return f"uploads/avatars/{filename}"

def delete_old_avatar(login):
    folder = app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(folder):
        return
    
    for filename in os.listdir(folder):
        if filename.startswith(login + '.'):
            old_file = os.path.join(folder, filename)
            if os.path.exists(old_file):
                os.remove(old_file)

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
        
        release_conn(conn)
        return instruments
        
    except Exception as e:
        print(f"Ошибка при получении инструментов: {e}")
        release_conn(conn)
        return []

def send_verification_email(email, verification_code):
    import threading
    def _send():
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
            msg.body = f"Ваш код подтверждения: {verification_code}\n\nКод действителен 24 часа."
            mail.send(msg)
            print(f"✓ Email с кодом подтверждения отправлен на {email}")
        except Exception as e:
            print(f"✗ Ошибка отправки email: {e}")

    ctx = app.app_context()
    def _send_with_ctx():
        with ctx:
            _send()

    thread = threading.Thread(target=_send_with_ctx)
    thread.daemon = True
    thread.start()
    return True

def allowed_repair_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_REPAIR_EXTENSIONS

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="Ошибка подключения к базе данных")
    
    cursor = conn.cursor()
    
    try:
        sql = """
        SELECT 
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
        WHERE i.is_available_for_sale = true
        ORDER BY i.views_count DESC, i.instrument_id DESC
        LIMIT 8
        """
        cursor.execute(sql)
        instruments = cursor.fetchall()
        
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('index.html', 
                             instruments=instruments, 
                             categories=categories)
    except Exception as e:
        release_conn(conn)
        return render_template('error.html', error=f"Ошибка при загрузке данных: {str(e)}")

@app.route('/catalog')
def catalog():
    category_id = request.args.get('category_id')
    search = request.args.get('search', '').strip()
    brand_id = request.args.get('brand_id')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    in_stock = request.args.get('in_stock')
    for_rent = request.args.get('for_rent')
    sort = request.args.get('sort', 'name_asc')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    where_conditions = ["i.is_available_for_sale = true"]
    params = []
    
    if search:
        where_conditions.append("(i.name ILIKE %s OR i.description ILIKE %s OR i.model ILIKE %s)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if category_id and category_id.isdigit():
        where_conditions.append("i.category_id = %s")
        params.append(int(category_id))
    
    if brand_id and brand_id.isdigit():
        where_conditions.append("i.brand_id = %s")
        params.append(int(brand_id))
    
    if price_min and price_min.isdigit():
        where_conditions.append("i.purchase_price >= %s")
        params.append(int(price_min))
    
    if price_max and price_max.isdigit():
        where_conditions.append("i.purchase_price <= %s")
        params.append(int(price_max))
    
    if in_stock == '1':
        where_conditions.append("i.quantity_in_stock > 0")
    
    if for_rent == '1':
        where_conditions.append("i.is_available_for_rent = true")
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    order_by = "i.name" 
    if sort == 'name_desc':
        order_by = "i.name DESC"
    elif sort == 'price_asc':
        order_by = "i.purchase_price ASC"
    elif sort == 'price_desc':
        order_by = "i.purchase_price DESC"
    elif sort == 'newest':
        order_by = "i.created_at DESC"
    elif sort == 'popular':
        order_by = "i.views_count DESC"
    
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
    ORDER BY {order_by}
    LIMIT %s OFFSET %s
    """
    
    pagination_params = params + [per_page, offset]
    cursor.execute(sql, pagination_params)
    
    columns = [column[0] for column in cursor.description]
    Instrument = namedtuple('Instrument', columns)
    instruments = [Instrument(*row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT brand_id, brand_name FROM brands ORDER BY brand_name")
    brands = cursor.fetchall()
    
    release_conn(conn)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
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
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', error="Ошибка подключения к базе данных")
        
        cursor = conn.cursor()
        
        cursor.execute("UPDATE instruments SET views_count = views_count + 1 WHERE instrument_id = %s", 
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
        WHERE i.instrument_id = %s
        """
        cursor.execute(sql, (instrument_id,))
        instrument_row = cursor.fetchone()
        
        if not instrument_row:
            flash('Инструмент не найден', 'danger')
            release_conn(conn)
            return redirect(url_for('catalog'))
        
        columns = [column[0] for column in cursor.description]
        instrument = {}
        for i, col in enumerate(columns):
            instrument[col] = instrument_row[i]
        
        similar_sql = """
        SELECT 
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
        WHERE i.category_id = %s 
        AND i.instrument_id != %s 
        AND i.is_available_for_sale = true 
        ORDER BY RANDOM()
        LIMIT 4
        """
        cursor.execute(similar_sql, (instrument['category_id'], instrument_id))
        similar = cursor.fetchall()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if 'rental_price_per_day' not in instrument or instrument['rental_price_per_day'] is None:
            instrument['rental_price_per_day'] = 0
        
        release_conn(conn)
        
        return render_template('instrument.html', 
                             instrument=instrument, 
                             similar=similar,
                             today=today)
        
    except Exception as e:
        print(f"Error in instrument_detail: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            try:
                release_conn(conn)
            except:
                pass
        return render_template('error.html', error=f"Ошибка при загрузке инструмента: {str(e)}")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
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
            WHERE u.login = %s AND u.is_active = true
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
                        SET email_verification_code = %s, email_verification_expires = %s
                        WHERE user_id = %s
                        """, (code_str, expires_at, user[0]))
                        conn.commit()
                        
                        send_verification_email(user[2], code_str)
                        
                        flash('Сначала подтвердите ваш email. Код отправлен на вашу почту.', 'warning')
                        release_conn(conn)
                        return redirect(url_for('verify_email'))
                    
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['user_name'] = f"{user[4]} {user[5]}"
                    session['user_role'] = user[18]
                    session['user_email'] = user[2]
                    session['user_avatar'] = user[11]
                    session['is_email_verified'] = True

                    flash(f'Добро пожаловать, {session["user_name"]}!', 'success')
                    release_conn(conn)
                    return redirect(url_for('index'))
                else:
                    flash('Неверный пароль', 'danger')
            else:
                flash('Пользователь не найден', 'danger')
            
            release_conn(conn)
        except Exception as e:
            release_conn(conn)
            flash(f'Ошибка при входе: {str(e)}', 'danger')
    
    return render_template('login.html')

@app.route('/api/check-unique', methods=['POST'])
def api_check_unique():
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
            
            release_conn(conn)
            return jsonify({'exists': exists})
        
        else:
            if field == 'login':
                cursor.execute("SELECT login FROM users WHERE login = %s", (value,))
            elif field == 'email':
                cursor.execute("SELECT email FROM users WHERE email = %s", (value,))
            else:
                release_conn(conn)
                return jsonify({'exists': False})
            
            result = cursor.fetchone()
            release_conn(conn)
            return jsonify({'exists': result is not None})
            
    except Exception as e:
        release_conn(conn)
        print(f"Ошибка при проверке уникальности: {e}")
        return jsonify({'exists': False})

@app.route('/api/check-email-dns', methods=['POST'])
def api_check_email_dns():
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
                WHERE login = %s OR email = %s
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
                release_conn(conn)
                return render_template('register.html', **form_data)
            
            verification_code = secrets.randbelow(900000) + 100000
            verification_code_str = str(verification_code)
            expires_at = datetime.now() + timedelta(hours=24)
            
            password_hash = hash_password(password)
            
            sql = """
            INSERT INTO users (login, email, password_hash, first_name, last_name, 
                             phone, role_id, is_active, is_email_verified,
                             email_verification_code, email_verification_expires)
            VALUES (%s, %s, %s, %s, %s, %s, 4, true, false, %s, %s)
            """
            cursor.execute(sql + " RETURNING user_id", (login, email, password_hash, first_name, last_name, phone,
                               verification_code_str, expires_at))
            user_id = cursor.fetchone()[0]
            conn.commit()
            
            release_conn(conn)
            
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
            release_conn(conn)
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            return render_template('register.html', **form_data)
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
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
            WHERE user_id = %s AND email = %s AND is_email_verified = false
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
                    SET is_email_verified = true, 
                        email_verification_code = NULL,
                        email_verification_expires = NULL
                    WHERE user_id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    cursor.execute("""
                    SELECT u.*, r.role_name, u.avatar_url
                    FROM users u
                    JOIN roles r ON u.role_id = r.role_id
                    WHERE u.user_id = %s
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
                    
                    release_conn(conn)
                    
                    flash('Email успешно подтвержден! Добро пожаловать в SoundGoodizer!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Неверный код подтверждения', 'danger')
            else:
                flash('Пользователь не найден или email уже подтвержден', 'danger')
            
            release_conn(conn)
        except Exception as e:
            release_conn(conn)
            flash(f'Ошибка при подтверждении email: {str(e)}', 'danger')
    
    return render_template('verify_email.html', email=email)

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
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
        SET email_verification_code = %s, email_verification_expires = %s
        WHERE user_id = %s AND email = %s AND is_email_verified = false
        """, (new_code_str, new_expires, user_id, email))
        
        if cursor.rowcount == 0:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Пользователь не найден или email уже подтвержден'})
        
        conn.commit()
        
        email_sent = send_verification_email(email, new_code_str)
        
        release_conn(conn)
        
        if email_sent:
            return jsonify({'success': True, 'message': 'Новый код отправлен на email'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка отправки email'})
            
    except Exception as e:
        release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/resend-password-code', methods=['POST'])
@login_required
def resend_password_code():
    code = secrets.randbelow(900000) + 100000
    session['password_change_code'] = str(code)
    session['password_change_expires'] = (datetime.now() + timedelta(minutes=15)).timestamp()
    
    msg = Message(
        subject='Повторный код смены пароля - SoundGoodizer',
        recipients=[session['user_email']]
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
                <p>Повторный код смены пароля</p>
            </div>
            
            <p>Здравствуйте, {session['user_name']}!</p>
            <p>Вы запросили новый код для смены пароля в вашем аккаунте SoundGoodizer.</p>
            
            <p>Ваш новый код подтверждения:</p>
            <div class="code">{code}</div>
            
            <p>Введите этот 6-значный код на странице профиля.</p>
            
            <p><strong>Код действителен 15 минут.</strong></p>
            
            <p>Если вы не запрашивали смену пароля, немедленно обратитесь в поддержку.</p>
            
            <hr>
            
            <p style="color: #666; font-size: 12px;">
                © SoundGoodizer. Все права защищены.<br>
                Это письмо отправлено автоматически, пожалуйста, не отвечайте на него.
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Новый код отправлен на вашу почту'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка отправки email: {str(e)}'})
    
@app.route('/logout')
def logout():
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
        
        if request.method == 'POST':
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename != '':
                    cursor.execute("SELECT login FROM users WHERE user_id = %s", (session['user_id'],))
                    user_login = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT avatar_url FROM users WHERE user_id = %s", (session['user_id'],))
                    old_avatar = cursor.fetchone()
                    old_avatar_path = old_avatar[0] if old_avatar else None
                    
                    if old_avatar_path and old_avatar_path.startswith('uploads/avatars/'):
                        old_filename = old_avatar_path.split('/')[-1]
                        old_filepath = os.path.join(app.root_path, 'static', old_avatar_path)
                        if os.path.exists(old_filepath):
                            try:
                                os.remove(old_filepath)
                            except:
                                pass
                    
                    avatar_path = save_avatar(file, user_login)
                    
                    if avatar_path:
                        cursor.execute("UPDATE users SET avatar_url = %s WHERE user_id = %s", 
                                     (avatar_path, session['user_id']))
                        conn.commit()
                        
                        session['user_avatar'] = avatar_path
                        flash('Фото профиля успешно обновлено', 'success')
                    else:
                        flash('Недопустимый формат файла', 'danger')
                    
                    release_conn(conn)
                    return redirect(url_for('profile'))
            
            if request.form.get('delete_avatar'):
                cursor.execute("SELECT avatar_url FROM users WHERE user_id = %s", (session['user_id'],))
                old_avatar = cursor.fetchone()
                
                if old_avatar and old_avatar[0]:
                    old_avatar_path = old_avatar[0]
                    if old_avatar_path.startswith('uploads/avatars/'):
                        old_filepath = os.path.join(app.root_path, 'static', old_avatar_path)
                        if os.path.exists(old_filepath):
                            try:
                                os.remove(old_filepath)
                            except:
                                pass
                
                cursor.execute("UPDATE users SET avatar_url = NULL WHERE user_id = %s", 
                             (session['user_id'],))
                conn.commit()
                
                session['user_avatar'] = None
                flash('Фото профиля удалено', 'success')
                
                release_conn(conn)
                return redirect(url_for('profile'))
            
            if request.form.get('change_password'):
                current_password = request.form.get('current_password', '').strip()
                new_password = request.form.get('new_password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()
                verification_code = request.form.get('verification_code', '').strip()
                
                cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (session['user_id'],))
                current_password_hash = cursor.fetchone()[0]
                
                errors = []
                if not current_password or not new_password or not confirm_password:
                    errors.append('Заполните все поля')
                elif new_password != confirm_password:
                    errors.append('Новые пароли не совпадают')
                elif len(new_password) < 6:
                    errors.append('Новый пароль должен содержать минимум 6 символов')
                else:
                    current_password_hash_input = hashlib.sha256(current_password.encode()).hexdigest()
                    if current_password_hash_input != current_password_hash:
                        errors.append('Текущий пароль неверен')
                
                if errors:
                    for error in errors:
                        flash(error, 'danger')
                    
                    form_data = {
                        'current_password': current_password,
                        'new_password': new_password,
                        'confirm_password': confirm_password,
                        'verification_code': verification_code if verification_code else ''
                    }
                    
                    release_conn(conn)
                    return redirect(url_for('profile', form_data=form_data))
                
                if 'password_change_code' not in session:
                    code = secrets.randbelow(900000) + 100000
                    session['password_change_code'] = str(code)
                    session['password_change_expires'] = (datetime.now() + timedelta(minutes=15)).timestamp()
                    
                    msg = Message(
                        subject='Подтверждение смены пароля - SoundGoodizer',
                        recipients=[session['user_email']]
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
                                <p>Подтверждение смены пароля</p>
                            </div>
                            
                            <p>Здравствуйте, {session['user_name']}!</p>
                            <p>Для смены пароля в вашем аккаунте SoundGoodizer необходим код подтверждения.</p>
                            
                            <p>Ваш код подтверждения:</p>
                            <div class="code">{code}</div>
                            
                            <p>Введите этот 6-значный код на странице профиля.</p>
                            
                            <p><strong>Код действителен 15 минут.</strong></p>
                            
                            <p>Если вы не запрашивали смену пароля, немедленно обратитесь в поддержку.</p>
                            
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
                    Здравствуйте, {session['user_name']}!
                    
                    Для смены пароля в вашем аккаунте SoundGoodizer необходим код подтверждения.
                    
                    Ваш код подтверждения: {code}
                    
                    Введите этот 6-значный код на странице профиля.
                    
                    Код действителен 15 минут.
                    
                    Если вы не запрашивали смену пароля, немедленно обратитесь в поддержку.
                    
                    © SoundGoodizer
                    """
                    
                    try:
                        mail.send(msg)
                        flash('Код подтверждения отправлен на вашу почту. Введите его для смены пароля.', 'info')
                    except Exception as e:
                        flash(f'Ошибка отправки email: {str(e)}', 'danger')
                    
                    release_conn(conn)
                    return redirect(url_for('profile'))
                
                if verification_code:
                    if 'password_change_expires' in session and datetime.now().timestamp() > session['password_change_expires']:
                        session.pop('password_change_code', None)
                        session.pop('password_change_expires', None)
                        flash('Срок действия кода истек. Запросите новый код.', 'danger')
                        release_conn(conn)
                        return redirect(url_for('profile'))
                    
                    if verification_code == session.get('password_change_code'):
                        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE user_id = %s",
                            (new_password_hash, session['user_id'])
                        )
                        conn.commit()
                        
                        session.pop('password_change_code', None)
                        session.pop('password_change_expires', None)
                        
                        flash('Пароль успешно изменен!', 'success')
                        release_conn(conn)
                        return redirect(url_for('profile') + '%spassword_changed=true')
                    else:
                        flash('Неверный код подтверждения', 'danger')
                else:
                    flash('Введите код подтверждения из письма', 'warning')
                
                release_conn(conn)
                return redirect(url_for('profile'))
        
        cursor.execute("""
            SELECT u.user_id, u.login, u.email, 
                   u.first_name, u.last_name, u.middle_name, 
                   u.phone, u.address, u.city, u.postal_code, 
                   u.avatar_url, u.is_email_verified, u.role_id, 
                   u.is_active, u.created_at,
                   r.role_name 
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (session['user_id'],))
        
        columns = [column[0] for column in cursor.description]
        user_row = cursor.fetchone()
        
        if not user_row:
            flash('Пользователь не найден', 'danger')
            release_conn(conn)
            return redirect(url_for('index'))
        
        user = dict(zip(columns, user_row))
        
        cursor.execute("SELECT COUNT(*) FROM cart_items WHERE user_id = %s", (session['user_id'],))
        cart_items = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE user_id = %s", (session['user_id'],))
        orders_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM rental_orders WHERE user_id = %s", (session['user_id'],))
        rentals_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM repair_requests WHERE user_id = %s", (session['user_id'],))
        repair_count = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT 'purchase' as type, order_number as number, order_date as date, status_name as status
            FROM purchase_orders po
            JOIN order_statuses os ON po.status_id = os.status_id
            WHERE po.user_id = %s
            
            UNION ALL
            
            SELECT 'rental' as type, rental_number as number, created_at as date, status_name as status
            FROM rental_orders ro
            JOIN rental_statuses rs ON ro.status_id = rs.status_id
            WHERE ro.user_id = %s
            
            UNION ALL
            
            SELECT 'repair' as type, request_number as number, created_at as date, status_name as status
            FROM repair_requests rr
            JOIN repair_statuses rs ON rr.status_id = rs.status_id
            WHERE rr.user_id = %s
            
            ORDER BY date DESC
            LIMIT 10 OFFSET 0
        """, (session['user_id'], session['user_id'], session['user_id']))

        recent_activities = cursor.fetchall()
        
        release_conn(conn)
        
        has_password_code = 'password_change_code' in session
        
        return render_template('profile.html',
                             user=user,
                             cart_items=cart_items,
                             orders_count=orders_count,
                             rentals_count=rentals_count,
                             repair_count=repair_count,
                             recent_activities=recent_activities,
                             has_password_code=has_password_code)
        
    except Exception as e:
        if conn:
            release_conn(conn)
        print(f"Error in profile: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка при загрузке профиля: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/check-current-password', methods=['POST'])
@login_required
def check_current_password():
    """Проверка текущего пароля"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'message': 'Нет данных'})
        
        current_password = data.get('current_password', '').strip()
        
        if not current_password:
            return jsonify({'valid': False, 'message': 'Пароль не указан'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'valid': False, 'message': 'Ошибка подключения к БД'})
        
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (session['user_id'],))
        result = cursor.fetchone()
        release_conn(conn)
        
        if not result:
            return jsonify({'valid': False, 'message': 'Пользователь не найден'})
        
        stored_hash = result[0]
        input_hash = hash_password(current_password)
        
        print(f"Stored hash: {stored_hash}")
        print(f"Input hash: {input_hash}")
        
        return jsonify({'valid': stored_hash == input_hash})
        
    except Exception as e:
        print(f"Error checking password: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'valid': False, 'message': str(e)})

@app.route('/api/search_suggestions')
def api_search_suggestions():
    """API для автодополнения поиска"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT 
            i.instrument_id,
            i.name,
            i.model,
            b.brand_name,
            i.main_image_url,
            i.purchase_price
        FROM instruments i
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        WHERE i.is_available_for_sale = true
          AND (i.name ILIKE %s OR i.model ILIKE %s OR b.brand_name ILIKE %s)
        ORDER BY 
            CASE 
                WHEN i.name ILIKE %s THEN 1
                WHEN i.model ILIKE %s THEN 2
                WHEN b.brand_name ILIKE %s THEN 3
                ELSE 4
            END,
            i.views_count DESC
        """
        
        search_term = f"%{query}%"
        params = [search_term, search_term, search_term, 
                  f"{query}%", f"{query}%", f"{query}%"]
        
        cursor.execute(sql, params)
        
        suggestions = []
        for row in cursor.fetchall():
            suggestions.append({
                'id': row[0],
                'name': row[1],
                'model': row[2],
                'brand': row[3],
                'image': row[4] if row[4] else 'img/default-instrument.jpg',
                'price': row[5],
                'url': url_for('instrument_detail', instrument_id=row[0])
            })
        
        release_conn(conn)
        return jsonify(suggestions)
        
    except Exception as e:
        print(f"Error in search suggestions: {e}")
        release_conn(conn)
        return jsonify([])

@app.route('/orders')
@login_required
def orders():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        purchase_sql = """
        SELECT 
            po.order_id,
            po.order_number,
            po.order_date,
            po.quantity,
            po.total_price,
            os.status_name,
            os.color_code as status_color,
            i.name as instrument_name,
            i.instrument_id,
            b.brand_name,
            i.main_image_url
        FROM purchase_orders po
        JOIN order_statuses os ON po.status_id = os.status_id
        JOIN instruments i ON po.instrument_id = i.instrument_id
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        WHERE po.user_id = %s
        ORDER BY po.order_date DESC
        LIMIT 10
        """
        cursor.execute(purchase_sql, (session['user_id'],))
        purchase_orders = cursor.fetchall()
        
        rental_sql = """
        SELECT 
            ro.rental_id,
            ro.rental_number,
            ro.created_at,
            ro.rental_start_date,
            ro.rental_end_date,
            ro.total_amount,
            ro.total_days,
            rs.status_name,
            rs.color_code as status_color,
            i.name as instrument_name,
            i.instrument_id,
            b.brand_name,
            i.main_image_url
        FROM rental_orders ro
        JOIN rental_statuses rs ON ro.status_id = rs.status_id
        JOIN instruments i ON ro.instrument_id = i.instrument_id
        LEFT JOIN brands b ON i.brand_id = b.brand_id
        WHERE ro.user_id = %s
        ORDER BY ro.created_at DESC
        """
        cursor.execute(rental_sql, (session['user_id'],))
        rental_orders = cursor.fetchall()

        repair_sql = """
        SELECT 
            rr.request_id,
            rr.request_number,
            rr.created_at,
            rr.customer_instrument_name,
            rr.brand,
            rr.model,
            rr.problem_description,
            rr.actual_cost,
            rs.status_name,
            rr.problem_photos_urls
        FROM repair_requests rr
        JOIN repair_statuses rs ON rr.status_id = rs.status_id
        WHERE rr.user_id = %s
        ORDER BY rr.created_at DESC
        """
        cursor.execute(repair_sql, (session['user_id'],))
        repair_requests = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('orders.html',
                             purchase_orders=purchase_orders,
                             rental_orders=rental_orders,
                             repair_requests=repair_requests)
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при загрузке заказов: {str(e)}', 'danger')
        return redirect(url_for('profile'))

@app.route('/add_to_rental_cart', methods=['POST'])
@login_required
def add_to_rental_cart():
    try:
        data = request.get_json()
        print(f"Received rental cart data: {data}")
        
        instrument_id = data.get('instrument_id')
        rental_start = data.get('rental_start')
        rental_end = data.get('rental_end')
        quantity = data.get('quantity', 1)
        
        if not all([instrument_id, rental_start, rental_end]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT quantity_in_stock, is_available_for_rent 
            FROM instruments 
            WHERE instrument_id = %s
        """, (instrument_id,))
        
        result = cursor.fetchone()
        if not result or result[1] == 0 or result[0] < quantity:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Инструмент недоступен для аренды'})
        
        cursor.execute("""
            SELECT cart_item_id, quantity 
            FROM cart_items 
            WHERE user_id = %s AND instrument_id = %s AND is_for_rental = 1
        """, (session['user_id'], instrument_id))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE cart_items 
                SET quantity = quantity + %s, 
                    rental_start_date = %s,
                    rental_end_date = %s
                WHERE cart_item_id = %s
            """, (quantity, rental_start, rental_end, existing[0]))
            print(f"Updated existing cart item: {existing[0]}")
        else:
            cursor.execute("""
                INSERT INTO cart_items 
                (user_id, instrument_id, quantity, is_for_rental, rental_start_date, rental_end_date)
                VALUES (%s, %s, %s, 1, %s, %s)
            """, (session['user_id'], instrument_id, quantity, rental_start, rental_end))
            print(f"Created new cart item")
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in add_to_rental_cart: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/cart')
@login_required
def cart():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        purchase_sql = """
        SELECT 
            ci.cart_item_id,
            ci.instrument_id,
            ci.quantity,
            i.name, 
            i.purchase_price, 
            i.main_image_url, 
            i.quantity_in_stock
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.user_id = %s AND ci.cart_item_id IS NOT NULL AND ci.quantity > 0 AND ci.is_for_rental = 0
        """
        cursor.execute(purchase_sql, (session['user_id'],))
        purchase_items = cursor.fetchall()
        
        rental_sql = """
        SELECT 
            ci.cart_item_id,
            ci.instrument_id,
            ci.quantity,
            i.name, 
            i.rental_price_per_day,
            i.main_image_url, 
            i.quantity_in_stock,
            ci.rental_start_date,
            ci.rental_end_date,
            i.purchase_price  -- Добавляем purchase_price для расчета залога
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.user_id = %s AND ci.cart_item_id IS NOT NULL AND ci.quantity > 0 AND ci.is_for_rental = 1
        """
        cursor.execute(rental_sql, (session['user_id'],))
        rental_items_raw = cursor.fetchall()
        
        purchase_list = []
        purchase_total = 0
        for item in purchase_items:
            item_total = item[2] * item[4]
            purchase_total += item_total
            
            image_url = item[5] if item[5] and item[5] != 'NULL' else 'img/default-instrument.jpg'
            
            purchase_list.append({
                'id': item[0],
                'instrument_id': item[1],
                'name': item[3],
                'price': item[4],
                'quantity': item[2],
                'image': image_url,
                'stock': item[6],
                'total': item_total,
                'is_for_rental': False
            })
        
        rental_list = []
        rental_total = 0
        deposit_total = 0
        total_days = 0
        
        for item in rental_items_raw:
            if item[7] and item[8]:
                try:
                    from datetime import datetime
                    start = datetime.strptime(str(item[7]), '%Y-%m-%d')
                    end = datetime.strptime(str(item[8]), '%Y-%m-%d')
                    days = (end - start).days
                    if days < 1:
                        days = 1
                except:
                    days = 1
            else:
                days = 1
            
            item_total = item[4] * days * item[2]
            
            deposit = item[9] * 0.1 * item[2]
            
            rental_total += item_total
            deposit_total += deposit
            total_days += days
            
            image_url = item[5] if item[5] and item[5] != 'NULL' else 'img/default-instrument.jpg'
            
            rental_list.append({
                'id': item[0],
                'instrument_id': item[1],
                'name': item[3],
                'daily_price': item[4],
                'quantity': item[2],
                'image': image_url,
                'stock': item[6],
                'rental_start': item[7] if item[7] else '',
                'rental_end': item[8] if item[8] else '',
                'purchase_price': item[9],
                'days': days,
                'total': item_total,
                'deposit': deposit,
                'is_for_rental': True
            })
        
        release_conn(conn)
        
        return render_template('cart.html', 
                             cart_items=purchase_list,
                             rental_items=rental_list,
                             purchase_total=purchase_total,
                             rental_total=rental_total,
                             deposit_total=deposit_total,
                             total_days=total_days)
    except Exception as e:
        print(f"Error in cart: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке корзины: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
@app.route('/add_to_cart/<int:instrument_id>')
@login_required
def add_to_cart(instrument_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(request.referrer or url_for('catalog'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT quantity_in_stock, name 
            FROM instruments 
            WHERE instrument_id = %s AND is_available_for_sale = true
        """, (instrument_id,))
        result = cursor.fetchone()
        
        if not result:
            flash('Товар не найден или недоступен для покупки', 'warning')
            release_conn(conn)
            return redirect(request.referrer or url_for('catalog'))
        
        stock, instrument_name = result
        
        if stock <= 0:
            flash('Товар отсутствует в наличии', 'warning')
            release_conn(conn)
            return redirect(request.referrer or url_for('catalog'))
        
        cursor.execute("""
            SELECT cart_item_id, quantity 
            FROM cart_items 
            WHERE user_id = %s AND instrument_id = %s AND cart_item_id IS NOT NULL
        """, (session['user_id'], instrument_id))
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing[1] + 1
            if new_quantity <= stock:
                cursor.execute("""
                    UPDATE cart_items 
                    SET quantity = %s 
                    WHERE cart_item_id = %s
                """, (new_quantity, existing[0]))
                flash(f'Добавлена еще одна единица "{instrument_name}"', 'success')
            else:
                flash(f'Недостаточно товара на складе. Осталось: {stock} шт.', 'warning')
        else:
            cursor.execute("""
                INSERT INTO cart_items (user_id, instrument_id, quantity, is_for_rental)
                VALUES (%s, %s, 1, 0)
            """, (session['user_id'], instrument_id))
            flash(f'Товар "{instrument_name}" добавлен в корзину', 'success')
        
        conn.commit()
        release_conn(conn)
        
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при добавлении в корзину: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('catalog'))

@app.route('/remove_from_cart/<int:cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('cart'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart_items WHERE cart_item_id = %s AND user_id = %s",
                      (cart_item_id, session['user_id']))
        conn.commit()
        release_conn(conn)
        
        flash('Товар удален из корзины', 'info')
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при удалении из корзины: {str(e)}', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/update_cart_item', methods=['POST'])
@login_required
def update_cart_item():
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    
    if not item_id or not quantity or quantity < 1:
        return jsonify({'success': False})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False})
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT ci.instrument_id, i.quantity_in_stock 
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.cart_item_id = %s AND ci.user_id = %s
        """, (item_id, session['user_id']))
        
        result = cursor.fetchone()
        if not result:
            release_conn(conn)
            return jsonify({'success': False})
        
        stock = result[1]
        if quantity > stock:
            quantity = stock
        
        cursor.execute("""
        UPDATE cart_items 
        SET quantity = %s 
        WHERE cart_item_id = %s AND user_id = %s
        """, (quantity, item_id, session['user_id']))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
    except Exception as e:
        release_conn(conn)
        return jsonify({'success': False})

@app.route('/checkout')
@login_required
def checkout():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('cart'))
    
    try:
        cursor = conn.cursor()
        
        sql = """
        SELECT ci.cart_item_id, ci.instrument_id, ci.quantity,
               i.name, i.purchase_price, i.main_image_url, i.quantity_in_stock
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.user_id = %s AND ci.cart_item_id IS NOT NULL AND ci.quantity > 0 AND ci.is_for_rental = 0
        """
        cursor.execute(sql, (session['user_id'],))
        cart_items = cursor.fetchall()
        
        if not cart_items:
            flash('Нет товаров для покупки', 'warning')
            release_conn(conn)
            return redirect(url_for('cart'))
        
        total = 0
        items_list = []
        for item in cart_items:
            item_total = item[2] * item[4]
            total += item_total
            
            items_list.append({
                'id': item[0],
                'instrument_id': item[1],
                'name': item[3],
                'price': item[4],
                'quantity': item[2],
                'image': item[5] if item[5] and item[5] != 'NULL' else 'img/default-instrument.jpg',
                'stock': item[6],
                'total': item_total
            })
        
        release_conn(conn)
        
        return render_template('checkout.html', cart_items=items_list, total=total)
        
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при оформлении заказа: {str(e)}', 'danger')
        return redirect(url_for('cart'))

@app.route('/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT ci.instrument_id, ci.quantity, i.purchase_price, i.name, i.quantity_in_stock
        FROM cart_items ci
        JOIN instruments i ON ci.instrument_id = i.instrument_id
        WHERE ci.user_id = %s AND ci.cart_item_id IS NOT NULL
        """, (session['user_id'],))
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Корзина пуста'})
        
        order_numbers = [] 
        
        for index, item in enumerate(cart_items):
            instrument_id, quantity, price, name, stock = item
            
            if stock < quantity:
                conn.rollback()
                release_conn(conn)
                return jsonify({
                    'success': False, 
                    'message': f'Товар "{name}" доступен только в количестве {stock} шт.'
                })
            
            item_total = price * quantity
            
            delivery_cost = data.get('delivery_cost', 0) if index == 0 else 0
            total_with_delivery = item_total + delivery_cost
            
            cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE DATE(order_date) = CURRENT_DATE")
            today_order_count = cursor.fetchone()[0]
            order_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{today_order_count + index + 1:04d}"
            
            cursor.execute("""
            INSERT INTO purchase_orders 
            (order_number, user_id, instrument_id, quantity, unit_price, total_price, 
             shipping_first_name, shipping_last_name, shipping_phone, 
             shipping_address, shipping_city, shipping_postal_code,
             delivery_method, delivery_cost, status_id, order_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW())
            """, (
                order_number,
                session['user_id'],
                instrument_id,
                quantity,
                price,
                total_with_delivery,
                data.get('first_name'),
                data.get('last_name'),
                data.get('phone'),
                data.get('address'),
                data.get('city'),
                data.get('postal_code'),
                data.get('delivery_method'),
                delivery_cost
            ))
            
            order_numbers.append(order_number)
            
            cursor.execute("""
            UPDATE instruments 
            SET quantity_in_stock = quantity_in_stock - %s
            WHERE instrument_id = %s
            """, (quantity, instrument_id))
        
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))
        
        conn.commit()
        release_conn(conn)
        
        if len(order_numbers) > 1:
            main_order = order_numbers[0] + f" (+{len(order_numbers)-1})"
        else:
            main_order = order_numbers[0]
        
        return jsonify({
            'success': True, 
            'order_number': main_order,
            'all_orders': order_numbers,
            'message': f'Создано {len(order_numbers)} заказ(ов). Основной номер: {main_order}'
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        print(f"Error creating order: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/rental_checkout')
@login_required
def rental_checkout():
    from datetime import datetime, timedelta
    
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('cart'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ci.cart_item_id,
                ci.instrument_id,
                ci.quantity,
                i.name,
                i.rental_price_per_day,
                i.main_image_url,
                b.brand_name,
                i.purchase_price
            FROM cart_items ci
            JOIN instruments i ON ci.instrument_id = i.instrument_id
            LEFT JOIN brands b ON i.brand_id = b.brand_id
            WHERE ci.user_id = %s AND ci.is_for_rental = 1
        """, (session['user_id'],))
        
        rental_items_raw = cursor.fetchall()
        
        if not rental_items_raw:
            flash('Нет товаров для аренды', 'warning')
            release_conn(conn)
            return redirect(url_for('cart'))
        
        items = []
        total_deposit = 0
        
        for item in rental_items_raw:
            items.append({
                'cart_item_id': item[0],
                'instrument_id': item[1],
                'quantity': item[2],
                'name': item[3],
                'daily_price': item[4],
                'image': item[5] if item[5] and item[5] != 'NULL' else 'img/default-instrument.jpg',
                'brand': item[6] if len(item) > 6 else '',
                'purchase_price': item[7]
            })
            
            total_deposit += item[7] * 0.1 * item[2]
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        release_conn(conn)
        
        return render_template('rental_checkout.html',
                             rental_items=items,
                             today=today,
                             default_start=tomorrow,
                             default_end=next_week,
                             total_deposit=total_deposit)
        
    except Exception as e:
        print(f"Error in rental_checkout: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке: {str(e)}', 'danger')
        return redirect(url_for('cart'))

@app.route('/create_rental_order', methods=['POST'])
@login_required
def create_rental_order():
    try:
        data = request.get_json()
        
        rental_start = data.get('rental_start')
        rental_end = data.get('rental_end')
        
        if not rental_start or not rental_end:
            return jsonify({'success': False, 'message': 'Не выбраны даты аренды'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ci.instrument_id, ci.quantity, i.rental_price_per_day, i.purchase_price
            FROM cart_items ci
            JOIN instruments i ON ci.instrument_id = i.instrument_id
            WHERE ci.user_id = %s AND ci.is_for_rental = 1
        """, (session['user_id'],))
        
        rental_items = cursor.fetchall()
        
        if not rental_items:
            return jsonify({'success': False, 'message': 'Нет товаров для аренды'})
        
        from datetime import datetime
        
        if hasattr(rental_start, 'strftime'):
            start_date = rental_start
            end_date = rental_end
        else:
            start_date = datetime.strptime(str(rental_start), '%Y-%m-%d').date()
            end_date = datetime.strptime(str(rental_end), '%Y-%m-%d').date()
        
        days = (end_date - start_date).days
        if days < 1:
            days = 1
        
        rental_subtotal = 0
        deposit_total = 0
        first_rental_id = None
        
        for index, item in enumerate(rental_items):
            subtotal = item[2] * days * item[1]
            deposit = item[3] * 0.1 * item[1]
            
            rental_subtotal += subtotal
            deposit_total += deposit
            
            temp_number = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{index}"
            
            cursor.execute("""
                INSERT INTO rental_orders 
                (rental_number, user_id, instrument_id, rental_start_date, rental_end_date,
                 daily_price, deposit_amount, total_amount,
                 delivery_address, status_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW())
                RETURNING rental_id
            """, (
                temp_number,
                session['user_id'],
                item[0],
                str(start_date),
                str(end_date),
                item[2],
                deposit,
                subtotal + deposit,
                data.get('delivery_address'),
            ))
            
            result = cursor.fetchone()
            if result and result[0]:
                rental_id = int(result[0])
                if first_rental_id is None:
                    first_rental_id = rental_id
            else:
                print(f"Warning: Could not get rental_id for item {index}")
            
            cursor.execute("""
                UPDATE instruments 
                SET quantity_in_stock = quantity_in_stock - %s
                WHERE instrument_id = %s
            """, (item[1], item[0]))
        
        if first_rental_id is None:
            conn.rollback()
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Не удалось создать запись аренды'})
        
        cursor.execute("SELECT rental_number FROM rental_orders WHERE rental_id = %s", (first_rental_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            rental_number = result[0]
        else:
            rental_number = "Неизвестный номер"
        
        cursor.execute("""
            DELETE FROM cart_items 
            WHERE user_id = %s AND is_for_rental = 1
        """, (session['user_id'],))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({
            'success': True,
            'rental_number': rental_number,
            'total': rental_subtotal + deposit_total,
            'deposit': deposit_total
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        print(f"Error creating rental: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/repair')
def repair():
    """Страница с информацией о ремонте"""
    return render_template('repair.html')

@app.route('/create_repair_request', methods=['GET', 'POST'])
@login_required
def create_repair_request():
    """Создание заявки на ремонт"""
    if request.method == 'POST':
        try:
            instrument_name = request.form.get('instrument_name', '').strip()
            brand = request.form.get('brand', '').strip()
            model = request.form.get('model', '').strip()
            problem_description = request.form.get('problem_description', '').strip()
            
            if not instrument_name or not problem_description:
                return jsonify({'success': False, 'message': 'Заполните все обязательные поля'})
            
            photos = request.files.getlist('photos')
            photo_urls = []
            
            if photos and photos[0] and photos[0].filename:
                os.makedirs(app.config['REPAIR_PHOTOS_FOLDER'], exist_ok=True)
                
                for photo in photos:
                    if photo and photo.filename and allowed_repair_file(photo.filename):
                        ext = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else 'jpg'
                        new_filename = f"repair_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                        
                        filepath = os.path.join(app.config['REPAIR_PHOTOS_FOLDER'], new_filename)
                        photo.save(filepath)
                        
                        photo_urls.append(f"uploads/repair_photos/{new_filename}")
            
            photos_json = ','.join(photo_urls) if photo_urls else None
            
            temp_number = f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO repair_requests 
                (request_number, user_id, customer_instrument_name, brand, model, 
                 problem_description, problem_photos_urls, status_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW())
                RETURNING request_id
            """, (
                temp_number,
                session['user_id'],
                instrument_name,
                brand,
                model,
                problem_description,
                photos_json
            ))
            
            request_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT request_number FROM repair_requests WHERE request_id = %s", (request_id,))
            request_number = cursor.fetchone()[0]
            
            conn.commit()
            release_conn(conn)
            
            return jsonify({'success': True, 'request_number': request_number})
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
                release_conn(conn)
            print(f"Error creating repair request: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)})
    
    return render_template('create_repair_request.html')

@app.route('/repair_requests')
@login_required
def repair_requests():
    """Список заявок пользователя на ремонт"""
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rr.request_id,
                rr.request_number,
                rr.customer_instrument_name,
                rr.brand,
                rr.model,
                rr.problem_description,
                rr.problem_photos_urls,
                rr.created_at,
                rr.actual_cost,
                rs.status_name,
                rs.color_code
            FROM repair_requests rr
            JOIN repair_statuses rs ON rr.status_id = rs.status_id
            WHERE rr.user_id = %s
            ORDER BY rr.created_at DESC
        """, (session['user_id'],))
        
        requests = cursor.fetchall()
        release_conn(conn)
        
        return render_template('repair_requests.html', requests=requests)
        
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при загрузке заявок: {str(e)}', 'danger')
        return redirect(url_for('profile'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
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
        
        cursor.execute("SELECT SUM(quantity_in_stock) FROM instruments")
        stats['instruments_stock'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM purchase_orders 
            WHERE DATE(order_date) = CURRENT_DATE
        """)
        stats['orders_today'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        stats['users_today'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM rental_orders 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        stats['rentals_today'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM repair_requests 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        stats['repairs_today'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(total_price) FROM purchase_orders 
            WHERE order_date >= NOW() - INTERVAL '1 month'
        """)
        stats['monthly_revenue'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT AVG(total_price) FROM purchase_orders
        """)
        stats['avg_order'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM rental_orders 
            WHERE status_id = (SELECT status_id FROM rental_statuses WHERE status_name = 'active')
        """)
        stats['active_rentals'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM repair_requests 
            WHERE status_id IN (
                SELECT status_id FROM repair_statuses 
                WHERE status_name IN ('new', 'diagnosed', 'in_progress')
            )
        """)
        stats['in_repair'] = cursor.fetchone()[0] or 0
        
        sql = """
        SELECT 
            po.order_id,
            po.order_number,
            po.order_date,
            po.total_price,
            u.login,
            os.status_name,
            u.avatar_url
        FROM purchase_orders po
        JOIN users u ON po.user_id = u.user_id
        JOIN order_statuses os ON po.status_id = os.status_id
        ORDER BY po.order_date DESC
        LIMIT 10
        """
        cursor.execute(sql)
        recent_orders = cursor.fetchall()
        
        sql = """
        SELECT 
            u.user_id,
            u.login,
            u.first_name,
            u.last_name,
            u.created_at,
            u.avatar_url
        FROM users u 
        ORDER BY u.created_at DESC
        LIMIT 5
        """
        cursor.execute(sql)
        recent_users = cursor.fetchall()
        
        release_conn(conn)
        
        now = datetime.now()
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_orders=recent_orders,
                             recent_users=recent_users,
                             now=now)
    except Exception as e:
        print(f"Error in admin_dashboard: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке админ-панели: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.login, u.email, u.first_name, u.last_name,
                   u.phone, u.is_active, u.created_at, r.role_name, u.avatar_url
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.created_at DESC
        LIMIT 5
        """)
        users = cursor.fetchall()
        release_conn(conn)
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        print(f"Error in admin_users: {e}")
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке пользователей: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/get_user/<int:user_id>')
@login_required
@admin_required
def admin_get_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Ошибка подключения к БД'})
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, login, email, first_name, last_name, phone, role_id, is_active
            FROM users WHERE user_id = %s
        """, (user_id,))
        
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        user = dict(zip(columns, row))
        release_conn(conn)
        
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        if conn:
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/admin/add_user', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    try:
        login = request.form.get('login')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        
        if not all([login, email, first_name, last_name, password, role_id]):
            flash('Заполните все обязательные поля', 'danger')
            return redirect(url_for('admin_users'))
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (login, email, password_hash, first_name, last_name, 
                             phone, role_id, is_active, is_email_verified, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true, true, NOW())
        """, (login, email, password_hash, first_name, last_name, phone, role_id))
        
        conn.commit()
        release_conn(conn)
        
        flash('Пользователь успешно добавлен', 'success')
        return redirect(url_for('admin_users'))
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        flash(f'Ошибка при добавлении пользователя: {str(e)}', 'danger')
        return redirect(url_for('admin_users'))

@app.route('/admin/edit_user', methods=['POST'])
@login_required
@admin_required
def admin_edit_user():
    try:
        user_id = request.form.get('user_id')
        login = request.form.get('login')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        is_active = request.form.get('is_active')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE (login = %s OR email = %s) AND user_id != %s
        """, (login, email, user_id))
        
        if cursor.fetchone():
            release_conn(conn)
            flash('Пользователь с таким логином или email уже существует', 'danger')
            return redirect(url_for('admin_users'))
        
        if password:
            password_hash = hash_password(password)
            cursor.execute("""
                UPDATE users 
                SET login = %s, email = %s, first_name = %s, last_name = %s, 
                    phone = %s, password_hash = %s, role_id = %s, is_active = %s
                WHERE user_id = %s
            """, (login, email, first_name, last_name, phone, password_hash, role_id, is_active, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET login = %s, email = %s, first_name = %s, last_name = %s, 
                    phone = %s, role_id = %s, is_active = %s
                WHERE user_id = %s
            """, (login, email, first_name, last_name, phone, role_id, is_active, user_id))
        
        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            cursor.execute("SELECT avatar_url FROM users WHERE user_id = %s", (user_id,))
            old_avatar = cursor.fetchone()
            if old_avatar and old_avatar[0]:
                old_path = os.path.join(app.root_path, 'static', old_avatar[0])
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            ext = avatar.filename.rsplit('.', 1)[1].lower()
            filename = f"{login}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar.save(filepath)
            
            cursor.execute("UPDATE users SET avatar_url = %s WHERE user_id = %s", 
                         (f"uploads/avatars/{filename}", user_id))
        
        conn.commit()
        release_conn(conn)
        
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('admin_users'))
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        flash(f'Ошибка при обновлении пользователя: {str(e)}', 'danger')
        return redirect(url_for('admin_users'))

@app.route('/admin/delete_user', methods=['POST'])
@login_required
@admin_required
def admin_delete_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id == session['user_id']:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'})
        
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.order_id, po.order_number, po.order_date,
                   po.total_price, os.status_name, u.login,
                   i.name as instrument_name, po.quantity,
                   i.main_image_url
            FROM purchase_orders po
            JOIN order_statuses os ON po.status_id = os.status_id
            JOIN users u ON po.user_id = u.user_id
            JOIN instruments i ON po.instrument_id = i.instrument_id
            ORDER BY po.order_date DESC
        LIMIT 10
        """)
        orders = cursor.fetchall()
        
        cursor.execute("SELECT * FROM order_statuses")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/orders.html', orders=orders, statuses=statuses)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заказов: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_orders'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.*, u.login, u.email, u.first_name, u.last_name, u.phone,
                   os.status_name, i.name as instrument_name,
                   b.brand_name, i.main_image_url
            FROM purchase_orders po
            JOIN users u ON po.user_id = u.user_id
            JOIN order_statuses os ON po.status_id = os.status_id
            JOIN instruments i ON po.instrument_id = i.instrument_id
            LEFT JOIN brands b ON i.brand_id = b.brand_id
            WHERE po.order_id = %s
        """, (order_id,))
        
        columns = [column[0] for column in cursor.description]
        order_row = cursor.fetchone()
        
        if not order_row:
            flash('Заказ не найден', 'danger')
            release_conn(conn)
            return redirect(url_for('admin_orders'))
        
        order = dict(zip(columns, order_row))
        
        cursor.execute("SELECT * FROM order_statuses")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/order_detail.html', order=order, statuses=statuses)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заказа: {str(e)}', 'danger')
        return redirect(url_for('admin_orders'))

@app.route('/admin/update_order_status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        status_id = data.get('status_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status_name FROM order_statuses WHERE status_id = %s", (status_id,))
        status_name = cursor.fetchone()[0]
        
        if status_name == 'shipped':
            cursor.execute("""
                UPDATE purchase_orders 
                SET status_id = %s, shipped_date = NOW()
                WHERE order_id = %s
            """, (status_id, order_id))
        elif status_name == 'delivered':
            cursor.execute("""
                UPDATE purchase_orders 
                SET status_id = %s, delivered_date = NOW()
                WHERE order_id = %s
            """, (status_id, order_id))
        elif status_name == 'cancelled':
            cursor.execute("""
                SELECT os.status_name, po.instrument_id, po.quantity
                FROM purchase_orders po
                JOIN order_statuses os ON po.status_id = os.status_id
                WHERE po.order_id = %s
            """, (order_id,))
            current = cursor.fetchone()
            if current and current[0] != 'cancelled':
                cursor.execute("""
                    UPDATE instruments
                    SET quantity_in_stock = quantity_in_stock + %s
                    WHERE instrument_id = %s
                """, (current[2], current[1]))
            cursor.execute("""
                UPDATE purchase_orders 
                SET status_id = %s, cancelled_date = NOW()
                WHERE order_id = %s
            """, (status_id, order_id))
        else:
            cursor.execute("""
                UPDATE purchase_orders 
                SET status_id = %s
                WHERE order_id = %s
            """, (status_id, order_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/rentals')
@login_required
@admin_required
def admin_rentals():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ro.rental_id, ro.rental_number, ro.rental_start_date,
                   ro.rental_end_date, ro.total_amount, rs.status_name,
                   u.login, i.name as instrument_name, i.main_image_url
            FROM rental_orders ro
            JOIN rental_statuses rs ON ro.status_id = rs.status_id
            JOIN users u ON ro.user_id = u.user_id
            JOIN instruments i ON ro.instrument_id = i.instrument_id
            ORDER BY ro.created_at DESC
        """)
        rentals = cursor.fetchall()
        
        cursor.execute("SELECT * FROM rental_statuses")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/rentals.html', rentals=rentals, statuses=statuses)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке аренд: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/update_rental_status', methods=['POST'])
@login_required
@admin_required
def admin_update_rental_status():
    try:
        data = request.get_json()
        rental_id = data.get('rental_id')
        status_id = data.get('status_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status_name FROM rental_statuses WHERE status_id = %s", (status_id,))
        status_name = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE rental_orders 
            SET status_id = %s
            WHERE rental_id = %s
        """, (status_id, rental_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        print(f"Error updating rental status: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/rental/<int:rental_id>')
@login_required
@admin_required
def admin_rental_detail(rental_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_rentals'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ro.*, u.login, u.email, u.first_name, u.last_name, u.phone,
                   rs.status_name, i.name as instrument_name,
                   b.brand_name, i.main_image_url
            FROM rental_orders ro
            JOIN users u ON ro.user_id = u.user_id
            JOIN rental_statuses rs ON ro.status_id = rs.status_id
            JOIN instruments i ON ro.instrument_id = i.instrument_id
            LEFT JOIN brands b ON i.brand_id = b.brand_id
            WHERE ro.rental_id = %s
        """, (rental_id,))
        
        columns = [column[0] for column in cursor.description]
        rental_row = cursor.fetchone()
        
        if not rental_row:
            flash('Аренда не найдена', 'danger')
            release_conn(conn)
            return redirect(url_for('admin_rentals'))
        
        rental = dict(zip(columns, rental_row))
        
        cursor.execute("SELECT * FROM rental_statuses")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/rental_detail.html', rental=rental, statuses=statuses)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке аренды: {str(e)}', 'danger')
        return redirect(url_for('admin_rentals'))

@app.route('/admin/repair_requests')
@login_required
@admin_required
def admin_repair_requests():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rr.request_id,
                rr.request_number,
                rr.customer_instrument_name,
                rr.brand,
                rr.model,
                rr.problem_description,
                rr.created_at,
                rr.actual_cost,
                rs.status_name,
                u.login,
                u.first_name,
                u.last_name,
                u.phone,
                u.email,
                rr.problem_photos_urls,
                rr.assigned_to
            FROM repair_requests rr
            JOIN repair_statuses rs ON rr.status_id = rs.status_id
            JOIN users u ON rr.user_id = u.user_id
            ORDER BY 
                CASE 
                    WHEN rs.sort_order <= 4 THEN 0 
                    ELSE 1 
                END,
                rr.created_at DESC
        """)
        
        requests = cursor.fetchall()
        
        cursor.execute("SELECT * FROM repair_statuses ORDER BY sort_order")
        statuses = cursor.fetchall()
        
        cursor.execute("""
            SELECT user_id, first_name, last_name 
            FROM users 
            WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'technician')
        """)
        technicians = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/repair_requests.html', 
                             requests=requests, 
                             statuses=statuses,
                             technicians=technicians)
        
    except Exception as e:
        print(f"Error in admin_repair_requests: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заявок: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/repair/<int:request_id>')
@login_required
@admin_required
def admin_repair_detail(request_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_repair_requests'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rr.*,
                u.login,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                rs.status_name,
                tech.first_name as tech_first_name,
                tech.last_name as tech_last_name
            FROM repair_requests rr
            JOIN users u ON rr.user_id = u.user_id
            JOIN repair_statuses rs ON rr.status_id = rs.status_id
            LEFT JOIN users tech ON rr.assigned_to = tech.user_id
            WHERE rr.request_id = %s
        """, (request_id,))
        
        columns = [column[0] for column in cursor.description]
        repair_row = cursor.fetchone()
        
        if not repair_row:
            flash('Заявка не найдена', 'danger')
            release_conn(conn)
            return redirect(url_for('admin_repair_requests'))
        
        repair = dict(zip(columns, repair_row))
        
        cursor.execute("SELECT * FROM repair_statuses ORDER BY sort_order")
        statuses = cursor.fetchall()
        
        cursor.execute("""
            SELECT user_id, first_name, last_name 
            FROM users 
            WHERE role_id = (SELECT role_id FROM roles WHERE role_name = 'technician')
        """)
        technicians = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('admin/repair_detail.html', 
                             repair=repair, 
                             statuses=statuses,
                             technicians=technicians)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заявки: {str(e)}', 'danger')
        return redirect(url_for('admin_repair_requests'))

@app.route('/admin/update_repair_status', methods=['POST'])
@login_required
@admin_required
def admin_update_repair_status():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        status_id = data.get('status_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status_name FROM repair_statuses WHERE status_id = %s", (status_id,))
        status_name = cursor.fetchone()[0]
        
        if status_name == 'completed':
            cursor.execute("""
                UPDATE repair_requests 
                SET status_id = %s, completed_at = NOW()
                WHERE request_id = %s
            """, (status_id, request_id))
        else:
            cursor.execute("""
                UPDATE repair_requests 
                SET status_id = %s
                WHERE request_id = %s
            """, (status_id, request_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/assign_repair_technician', methods=['POST'])
@login_required
@admin_required
def admin_assign_repair_technician():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        technician_id = data.get('technician_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE repair_requests 
            SET assigned_to = %s
            WHERE request_id = %s
        """, (technician_id if technician_id else None, request_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/set_repair_cost', methods=['POST'])
@login_required
@admin_required
def admin_set_repair_cost():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        cost = data.get('cost')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE repair_requests 
            SET actual_cost = %s
            WHERE request_id = %s
        """, (cost, request_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/brands')
@login_required
@admin_required
def admin_brands():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brands ORDER BY brand_name")
        brands = cursor.fetchall()
        release_conn(conn)
        
        return render_template('admin/brands.html', brands=brands)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке брендов: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_brand', methods=['POST'])
@login_required
@admin_required
def admin_add_brand():
    try:
        brand_name = request.form.get('brand_name')
        country = request.form.get('country')
        description = request.form.get('description')
        website = request.form.get('website')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO brands (brand_name, country, description, website)
            VALUES (%s, %s, %s, %s)
        """, (brand_name, country, description, website))
        
        conn.commit()
        release_conn(conn)
        
        flash('Бренд успешно добавлен', 'success')
        return redirect(url_for('admin_brands'))
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        flash(f'Ошибка при добавлении бренда: {str(e)}', 'danger')
        return redirect(url_for('admin_brands'))

@app.route('/admin/edit_brand', methods=['POST'])
@login_required
@admin_required
def admin_edit_brand():
    try:
        brand_id = request.form.get('brand_id')
        brand_name = request.form.get('brand_name')
        country = request.form.get('country')
        description = request.form.get('description')
        website = request.form.get('website')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE brands 
            SET brand_name = %s, country = %s, description = %s, website = %s
            WHERE brand_id = %s
        """, (brand_name, country, description, website, brand_id))
        
        conn.commit()
        release_conn(conn)
        
        flash('Бренд успешно обновлен', 'success')
        return redirect(url_for('admin_brands'))
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        flash(f'Ошибка при обновлении бренда: {str(e)}', 'danger')
        return redirect(url_for('admin_brands'))

@app.route('/admin/instruments')
@login_required
@admin_required
def admin_instruments():
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
        
        release_conn(conn)
        
        return render_template('admin/instruments.html',
                             instruments=instruments,
                             categories=categories,
                             brands=brands,
                             conditions=conditions)
    except Exception as e:
        release_conn(conn)
        flash(f'Ошибка при загрузке инструментов: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/get_instrument/<int:instrument_id>')
@login_required
@admin_required
def admin_get_instrument(instrument_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Ошибка подключения к БД'})
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM instruments WHERE instrument_id = %s
        """, (instrument_id,))
        
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Инструмент не найден'})
        
        instrument = dict(zip(columns, row))
        release_conn(conn)
        
        return jsonify({'success': True, 'instrument': instrument})
    except Exception as e:
        if conn:
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/admin/add_instrument', methods=['POST'])
@login_required
@admin_required
def admin_add_instrument():
    try:
        name = request.form.get('name')
        model = request.form.get('model')
        brand_id = request.form.get('brand_id') or None
        category_id = request.form.get('category_id') or None
        year_of_manufacture = request.form.get('year_of_manufacture') or None
        purchase_price = request.form.get('purchase_price')
        rental_price_per_day = request.form.get('rental_price_per_day') or None
        quantity_in_stock = request.form.get('quantity_in_stock') or 1
        condition_id = request.form.get('condition_id') or None
        description = request.form.get('description')
        characteristics = request.form.get('characteristics')
        is_available_for_sale = true if request.form.get('is_available_for_sale') else 0
        is_available_for_rent = true if request.form.get('is_available_for_rent') else 0
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO instruments 
            (name, model, brand_id, category_id, year_of_manufacture, purchase_price, 
             rental_price_per_day, quantity_in_stock, condition_id, description, 
             characteristics, is_available_for_sale, is_available_for_rent, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING instrument_id
        """, (name, model, brand_id, category_id, year_of_manufacture, purchase_price,
              rental_price_per_day, quantity_in_stock, condition_id, description,
              characteristics, is_available_for_sale, is_available_for_rent))
        
        instrument_id = cursor.fetchone()[0]
        
        main_image = request.files.get('main_image')
        if main_image and main_image.filename:
            os.makedirs(app.config['INSTRUMENT_IMAGES_FOLDER'], exist_ok=True)
            
            ext = main_image.filename.rsplit('.', 1)[1].lower()
            filename = f"{instrument_id}.{ext}"
            filepath = os.path.join(app.config['INSTRUMENT_IMAGES_FOLDER'], filename)
            
            main_image.save(filepath)
            
            cursor.execute("""
                UPDATE instruments 
                SET main_image_url = %s 
                WHERE instrument_id = %s
            """, (f"img/instruments/{filename}", instrument_id))
        
        conn.commit()
        release_conn(conn)
        
        flash('Инструмент успешно добавлен', 'success')
        return redirect(url_for('admin_instruments'))
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        flash(f'Ошибка при добавлении инструмента: {str(e)}', 'danger')
        return redirect(url_for('admin_instruments'))

@app.route('/admin/update_instrument', methods=['POST'])
@login_required
@admin_required
def admin_update_instrument():
    try:
        instrument_id = request.form.get('instrument_id')
        name = request.form.get('name')
        model = request.form.get('model')
        brand_id = request.form.get('brand_id') or None
        category_id = request.form.get('category_id') or None
        year_of_manufacture = request.form.get('year_of_manufacture') or None
        purchase_price = request.form.get('purchase_price')
        rental_price_per_day = request.form.get('rental_price_per_day') or None
        quantity_in_stock = request.form.get('quantity_in_stock') or 1
        condition_id = request.form.get('condition_id') or None
        description = request.form.get('description')
        characteristics = request.form.get('characteristics')
        is_available_for_sale = true if request.form.get('is_available_for_sale') else 0
        is_available_for_rent = true if request.form.get('is_available_for_rent') else 0
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        main_image = request.files.get('main_image')
        
        if main_image and main_image.filename:
            os.makedirs(app.config['INSTRUMENT_IMAGES_FOLDER'], exist_ok=True)
            
            ext = main_image.filename.rsplit('.', 1)[1].lower()
            filename = f"{instrument_id}.{ext}"
            filepath = os.path.join(app.config['INSTRUMENT_IMAGES_FOLDER'], filename)
            
            cursor.execute("SELECT main_image_url FROM instruments WHERE instrument_id = %s", (instrument_id,))
            old_image = cursor.fetchone()
            if old_image and old_image[0]:
                old_filepath = os.path.join('static', old_image[0])
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            main_image.save(filepath)
            
            cursor.execute("""
                UPDATE instruments 
                SET name = %s, model = %s, brand_id = %s, category_id = %s, 
                    year_of_manufacture = %s, purchase_price = %s, rental_price_per_day = %s,
                    quantity_in_stock = %s, condition_id = %s, description = %s, 
                    characteristics = %s, is_available_for_sale = %s, is_available_for_rent = %s,
                    main_image_url = %s
                WHERE instrument_id = %s
            """, (name, model, brand_id, category_id, year_of_manufacture, purchase_price,
                  rental_price_per_day, quantity_in_stock, condition_id, description,
                  characteristics, is_available_for_sale, is_available_for_rent,
                  f"img/instruments/{filename}", instrument_id))
        else:
            cursor.execute("""
                UPDATE instruments 
                SET name = %s, model = %s, brand_id = %s, category_id = %s, 
                    year_of_manufacture = %s, purchase_price = %s, rental_price_per_day = %s,
                    quantity_in_stock = %s, condition_id = %s, description = %s, 
                    characteristics = %s, is_available_for_sale = %s, is_available_for_rent = %s
                WHERE instrument_id = %s
            """, (name, model, brand_id, category_id, year_of_manufacture, purchase_price,
                  rental_price_per_day, quantity_in_stock, condition_id, description,
                  characteristics, is_available_for_sale, is_available_for_rent, instrument_id))
        
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_instrument', methods=['POST'])
@login_required
@admin_required
def admin_delete_instrument():
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE instrument_id = %s", (instrument_id,))
        orders_count = cursor.fetchone()[0]
        
        if orders_count > 0:
            release_conn(conn)
            return jsonify({'success': False, 'message': 'Нельзя удалить инструмент, по которому есть заказы'})
        
        cursor.execute("DELETE FROM instruments WHERE instrument_id = %s", (instrument_id,))
        conn.commit()
        release_conn(conn)
        
        return jsonify({'success': True})
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            release_conn(conn)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/technician/repair_requests')
@login_required
@technician_required
def technician_repair_requests():
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        if session['user_role'] == 'technician':
            cursor.execute("""
                SELECT 
                    rr.request_id,
                    rr.request_number,
                    rr.customer_instrument_name,
                    rr.brand,
                    rr.model,
                    rr.problem_description,
                    rr.created_at,
                    rr.actual_cost,
                    rs.status_name,
                    u.login,
                    u.first_name,
                    u.last_name,
                    u.phone,
                    u.email,
                    rr.problem_photos_urls
                FROM repair_requests rr
                JOIN repair_statuses rs ON rr.status_id = rs.status_id
                JOIN users u ON rr.user_id = u.user_id
                WHERE rr.assigned_to = %s OR rr.assigned_to IS NULL
                ORDER BY 
                    CASE 
                        WHEN rr.assigned_to = %s THEN 0
                        ELSE 1
                    END,
                    rr.created_at DESC
            """, (session['user_id'], session['user_id']))
        else:
            cursor.execute("""
                SELECT 
                    rr.request_id,
                    rr.request_number,
                    rr.customer_instrument_name,
                    rr.brand,
                    rr.model,
                    rr.problem_description,
                    rr.created_at,
                    rr.actual_cost,
                    rs.status_name,
                    u.login,
                    u.first_name,
                    u.last_name,
                    u.phone,
                    u.email,
                    rr.problem_photos_urls,
                    rr.assigned_to
                FROM repair_requests rr
                JOIN repair_statuses rs ON rr.status_id = rs.status_id
                JOIN users u ON rr.user_id = u.user_id
                ORDER BY 
                    CASE 
                        WHEN rs.sort_order <= 4 THEN 0 
                        ELSE 1 
                    END,
                    rr.created_at DESC
            """)
        
        requests = cursor.fetchall()
        
        cursor.execute("SELECT * FROM repair_statuses ORDER BY sort_order")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('technician/repair_requests.html', 
                             requests=requests, 
                             statuses=statuses,
                             is_technician=(session['user_role'] == 'technician'))
        
    except Exception as e:
        print(f"Error in technician_repair_requests: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заявок: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
@app.route('/technician/repair/<int:request_id>')
@login_required
@technician_required
def technician_repair_detail(request_id):
    conn = get_db_connection()
    if not conn:
        flash('Ошибка подключения к базе данных', 'danger')
        return redirect(url_for('technician_repair_requests'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rr.*,
                u.login,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                rs.status_name,
                tech.first_name as tech_first_name,
                tech.last_name as tech_last_name
            FROM repair_requests rr
            JOIN users u ON rr.user_id = u.user_id
            JOIN repair_statuses rs ON rr.status_id = rs.status_id
            LEFT JOIN users tech ON rr.assigned_to = tech.user_id
            WHERE rr.request_id = %s
        """, (request_id,))
        
        columns = [column[0] for column in cursor.description]
        repair_row = cursor.fetchone()
        
        if not repair_row:
            flash('Заявка не найдена', 'danger')
            release_conn(conn)
            return redirect(url_for('technician_repair_requests'))
        
        repair = dict(zip(columns, repair_row))
        
        cursor.execute("SELECT * FROM repair_statuses ORDER BY sort_order")
        statuses = cursor.fetchall()
        
        release_conn(conn)
        
        return render_template('technician/repair_detail.html', 
                             repair=repair, 
                             statuses=statuses)
    except Exception as e:
        if conn:
            release_conn(conn)
        flash(f'Ошибка при загрузке заявки: {str(e)}', 'danger')
        return redirect(url_for('technician_repair_requests'))

@app.route('/api/cart_count')
def api_cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'count': 0})
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(quantity) FROM cart_items WHERE user_id = %s", 
                      (session['user_id'],))
        result = cursor.fetchone()
        count = result[0] if result[0] else 0
        release_conn(conn)
        return jsonify({'count': count})
    except:
        release_conn(conn)
        return jsonify({'count': 0})

@app.route('/api/categories')
def api_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        release_conn(conn)
        
        result = [{'id': c[0], 'name': c[1]} for c in categories]
        return jsonify(result)
    except:
        release_conn(conn)
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
        
        release_conn(conn)
    else:
        print("❌ ОШИБКА: Не удалось подключиться к базе данных")
    
    print("=" * 50)
    print("Сервер запускается на http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)