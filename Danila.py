import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'danila-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///danila.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

# Модель типа пинка
class KickType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    damage = db.Column(db.Integer, default=1)
    kicks = db.relationship('Kick', backref='kick_type', lazy=True)

# Модель пинка
class Kick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kicker_name = db.Column(db.String(100), nullable=False)
    power = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    kick_type_id = db.Column(db.Integer, db.ForeignKey('kick_type.id'))
    image = db.Column(db.String(100))  # картинка пинка

# Модель Данилы
class Danila(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Данила')
    health = db.Column(db.Integer, default=100)
    total_kicks_received = db.Column(db.Integer, default=0)
    last_kicked = db.Column(db.DateTime)

# Инициализация БД с типами пинков
def init_db():
    with app.app_context():
        db.create_all()
        
        # Создаем основные типы пинков, если их нет
        if not KickType.query.first():
            default_kicks = [
                {'name': 'Легкий щелбан', 'damage': 1},
                {'name': 'Средний пинок', 'damage': 3},
                {'name': 'Мощный удар', 'damage': 5},
                {'name': 'Сверхсильный пинок', 'damage': 10},
                {'name': 'Ультра-мега-пинок', 'damage': 15}
            ]
            for kick_data in default_kicks:
                kick_type = KickType(name=kick_data['name'], damage=kick_data['damage'])
                db.session.add(kick_type)
            
            # Создаем Данилу, если его нет
            if not Danila.query.first():
                danila = Danila(name='Данила', health=100, total_kicks_received=0)
                db.session.add(danila)
            
            db.session.commit()

# Главная страница со статистикой пинков
@app.route('/')
def index():
    kick_type_id = request.args.get('kick_type_id', type=int)
    search_query = request.args.get('q', '')
    
    # Базовый запрос для пинков
    query = Kick.query
    
    # Фильтрация по типу пинка
    if kick_type_id:
        query = query.filter(Kick.kick_type_id == kick_type_id)
    
    # Поиск по имени пинающего
    if search_query:
        query = query.filter(Kick.kicker_name.ilike(f'%{search_query}%'))
    
    kicks = query.order_by(Kick.timestamp.desc()).limit(50).all()
    kick_types = KickType.query.order_by(KickType.damage).all()
    danila = Danila.query.first()
    
    # Статистика
    total_kicks = Kick.query.count()
    today_kicks = Kick.query.filter(
        db.func.date(Kick.timestamp) == datetime.today().date()
    ).count()
    
    return render_template('index.html', 
                         kicks=kicks, 
                         kick_types=kick_types, 
                         danila=danila,
                         selected_kick_type_id=kick_type_id,
                         search_query=search_query,
                         total_kicks=total_kicks,
                         today_kicks=today_kicks)

# Пинание Данилы
@app.route('/kick_danila', methods=['POST'])
def kick_danila():
    danila = Danila.query.first()
    if not danila:
        flash('Данила не найден!', 'error')
        return redirect(url_for('index'))

    try:
        kick_type_id = request.form.get('kick_type_id')
        kick_type = KickType.query.get(kick_type_id) if kick_type_id else None
        
        # Создаем запись о пинке
        kick = Kick(
            kicker_name=request.form['kicker_name'] or 'Аноним',
            power=kick_type.damage if kick_type else 1,
            kick_type_id=kick_type_id
        )
        
        # Обновляем здоровье Данилы
        damage = kick_type.damage if kick_type else 1
        danila.health = max(0, danila.health - damage)
        danila.total_kicks_received += 1
        danila.last_kicked = datetime.utcnow()
        
        db.session.add(kick)
        db.session.commit()
        
        # Проверяем, не "умер" ли Данила
        if danila.health <= 0:
            flash(f'Данила получил смертельный удар от {kick.kicker_name}! 💀', 'error')
        else:
            flash(f'Данила успешно пиннут пользователем {kick.kicker_name}! 💥', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка пинка: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Лечение Данилы
@app.route('/heal_danila', methods=['POST'])
def heal_danila():
    danila = Danila.query.first()
    if not danila:
        flash('Данила не найден!', 'error')
        return redirect(url_for('index'))

    try:
        heal_amount = int(request.form.get('heal_amount', 20))
        danila.health = min(100, danila.health + heal_amount)
        db.session.commit()
        flash(f'Данила вылечен на {heal_amount} HP! ❤️', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка лечения: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Сброс Данилы (новый Данила)
@app.route('/reset_danila', methods=['POST'])
def reset_danila():
    try:
        danila = Danila.query.first()
        if danila:
            danila.health = 100
            danila.total_kicks_received = 0
            danila.last_kicked = None
            db.session.commit()
            flash('Данила полностью восстановлен! 🔄', 'success')
        else:
            new_danila = Danila(name='Данила', health=100, total_kicks_received=0)
            db.session.add(new_danila)
            db.session.commit()
            flash('Создан новый Данила! 👶', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка сброса: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Добавление нового типа пинка
@app.route('/add_kick_type', methods=['POST'])
def add_kick_type():
    kick_name = request.form.get('kick_name', '').strip()
    damage = request.form.get('damage', 1, type=int)
    
    if not kick_name:
        flash('Введите название пинка', 'error')
        return redirect(url_for('index'))
    
    try:
        if KickType.query.filter_by(name=kick_name).first():
            flash('Такой тип пинка уже существует', 'error')
        else:
            kick_type = KickType(name=kick_name, damage=damage)
            db.session.add(kick_type)
            db.session.commit()
            flash('Тип пинка успешно добавлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка добавления: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# API для получения статистики (может пригодиться для AJAX)
@app.route('/api/danila_status')
def danila_status():
    danila = Danila.query.first()
    if danila:
        return jsonify({
            'health': danila.health,
            'total_kicks': danila.total_kicks_received,
            'last_kicked': danila.last_kicked.isoformat() if danila.last_kicked else None
        })
    return jsonify({'error': 'Данила не найден'})

# Удаление записи о пинке
@app.route('/delete_kick/<int:kick_id>', methods=['POST'])
def delete_kick(kick_id):
    kick = Kick.query.get(kick_id)
    if not kick:
        flash('Запись о пинке не найдена', 'error')
        return redirect(url_for('index'))

    try:
        db.session.delete(kick)
        db.session.commit()
        flash('Запись о пинке удалена', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=True)
