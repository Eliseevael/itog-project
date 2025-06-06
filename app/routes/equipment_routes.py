from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Equipment
from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.models import Equipment, Category, Photo
from app import db
import os, hashlib
from datetime import datetime
from flask_login import current_user
from config import Config

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/')
@login_required
def index():
    equipment_list = Equipment.query.all()
    return render_template('equipment_list.html', equipment_list=equipment_list)

@equipment_bp.route('/add', methods=['GET', 'POST'])
def add_equipment():
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form['name']
        inv_number = request.form['inventory_number']
        category_id = request.form['category_id']
        date_str = request.form['purchase_date']
        cost = request.form['cost']
        status = request.form['status']
        note = request.form['note']
        file = request.files['photo']

        # Парсим дату
        try:
            purchase_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты.', 'danger')
            return redirect(url_for('equipment.add_equipment'))

        # Проверка и сохранение изображения
        photo_id = None
        if file and file.filename != '':
            file_data = file.read()
            file_hash = hashlib.md5(file_data).hexdigest()
            existing = Photo.query.filter_by(md5_hash=file_hash).first()

            if existing:
                photo_id = existing.id
            else:
                mime = file.mimetype
                filename = secure_filename(file.filename)
                new_photo = Photo(
                    filename=filename,
                    mime_type=mime,
                    md5_hash=file_hash
                )
                db.session.add(new_photo)
                db.session.flush()  # получаем id до commit
                photo_id = new_photo.id

                # Сохраняем файл на диск
                filepath = os.path.join(Config.UPLOAD_FOLDER, f"{photo_id}_{filename}")
                with open(filepath, 'wb') as f:
                    f.write(file_data)

        # Добавляем оборудование
        equipment = Equipment(
            name=name,
            inventory_number=inv_number,
            category_id=category_id,
            purchase_date=purchase_date,
            cost=cost,
            status=status,
            note=note
        )
        db.session.add(equipment)
        db.session.flush()  # чтобы получить ID

        if photo_id:
            photo = Photo.query.get(photo_id)
            photo.equipment_id = equipment.id

        db.session.commit()
        flash('Оборудование успешно добавлено!', 'success')
        return redirect(url_for('equipment.index'))

    return render_template('equipment_add.html', categories=categories)