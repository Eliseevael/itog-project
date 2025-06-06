from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Equipment, Category, Photo, Maintenance, WriteOff
from app import db
from config import Config
from app.form import MaintenanceForm, WriteOffForm
import os
import hashlib
from datetime import datetime
from flask import make_response
from weasyprint import HTML
from flask import render_template_string

equipment_bp = Blueprint('equipment', __name__, template_folder='../templates')


@equipment_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Equipment.query

    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        try:
            query = query.filter(Equipment.purchase_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except: pass
    if date_to:
        try:
            query = query.filter(Equipment.purchase_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except: pass

    equipment_list = query.order_by(Equipment.purchase_date.desc()).paginate(page=page, per_page=10)
    categories = Category.query.all()

    return render_template('equipment_list.html', equipment_list=equipment_list, categories=categories, int=int)


@equipment_bp.route('/add', methods=['GET', 'POST'])
@login_required
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

        if Equipment.query.filter_by(inventory_number=inv_number).first():
            flash('Инвентарный номер уже существует. Введите уникальный.', 'danger')
            return redirect(url_for('equipment.add_equipment'))

        try:
            purchase_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты.', 'danger')
            return redirect(url_for('equipment.add_equipment'))

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
                new_photo = Photo(filename=filename, mime_type=mime, md5_hash=file_hash)
                db.session.add(new_photo)
                db.session.flush()
                photo_id = new_photo.id
                filepath = os.path.join(Config.UPLOAD_FOLDER, f"{photo_id}_{filename}")
                with open(filepath, 'wb') as f:
                    f.write(file_data)

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
        db.session.flush()

        if photo_id:
            photo = Photo.query.get(photo_id)
            photo.equipment_id = equipment.id

        if status == 'written_off':
            record = WriteOff(
                equipment_id=equipment.id,
                reason='Списано при добавлении.',
                pdf_filename='manual_entry.pdf'
            )
            db.session.add(record)

        try:
            db.session.commit()
            flash('Оборудование успешно добавлено!', 'success')
            return redirect(url_for('equipment.index'))
        except Exception as e:
            db.session.rollback()
            print("❌ Ошибка при сохранении оборудования:", e)
            flash('Ошибка при сохранении оборудования.', 'danger')
            return redirect(url_for('equipment.add_equipment'))


    return render_template('equipment_add.html', categories=categories)


@equipment_bp.route('/view/<int:id>', methods=['GET', 'POST'])
@login_required
def view_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    history = Maintenance.query.filter_by(equipment_id=id).order_by(Maintenance.date.desc()).all()
    form = MaintenanceForm()

    if form.validate_on_submit() and current_user.role.name in ['admin', 'tech']:
        record = Maintenance(
            equipment_id=equipment.id,
            date=form.date.data,
            type=form.type.data,
            comment=form.comment.data
        )
        db.session.add(record)
        db.session.commit()
        flash('Запись об обслуживании добавлена.', 'success')
        return redirect(url_for('equipment.view_equipment', id=id))

    photo_path = None
    if equipment.photo:
        photo_path = url_for('static', filename=f"uploads/{equipment.photo.id}_{equipment.photo.filename}")

    return render_template('equipment_view.html', equipment=equipment, history=history, photo_path=photo_path, form=form)


@equipment_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    if current_user.role.name != 'admin':
        flash('У вас недостаточно прав для выполнения данного действия.', 'danger')
        return redirect(url_for('equipment.index'))

    equipment = Equipment.query.get_or_404(id)

    # Удаление записи о списании, если есть
    writeoff_record = WriteOff.query.filter_by(equipment_id=equipment.id).first()
    if writeoff_record:
        db.session.delete(writeoff_record)

    # Удаление фото с диска, если есть
    if equipment.photo:
        path = os.path.join(Config.UPLOAD_FOLDER, f"{equipment.photo.id}_{equipment.photo.filename}")
        if os.path.exists(path):
            os.remove(path)

    try:
        db.session.delete(equipment)
        db.session.commit()
        flash(f'Оборудование "{equipment.name}" удалено.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении.', 'danger')

    return redirect(url_for('equipment.index'))


@equipment_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    if current_user.role.name != 'admin':
        flash('У вас недостаточно прав.', 'danger')
        return redirect(url_for('equipment.index'))

    equipment = Equipment.query.get_or_404(id)
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

        existing = Equipment.query.filter_by(inventory_number=inv_number).first()
        if existing and existing.id != equipment.id:
            flash('Инвентарный номер уже занят другим оборудованием.', 'danger')
            return redirect(url_for('equipment.edit_equipment', id=id))

        try:
            purchase_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты.', 'danger')
            return redirect(url_for('equipment.edit_equipment', id=id))

        equipment.name = name
        equipment.inventory_number = inv_number
        equipment.category_id = category_id
        equipment.purchase_date = purchase_date
        equipment.cost = cost
        equipment.status = status
        equipment.note = note

        if file and file.filename != '':
            file_data = file.read()
            file_hash = hashlib.md5(file_data).hexdigest()
            existing_photo = Photo.query.filter_by(md5_hash=file_hash).first()
            if not existing_photo:
                mime = file.mimetype
                filename = secure_filename(file.filename)
                new_photo = Photo(filename=filename, mime_type=mime, md5_hash=file_hash)
                db.session.add(new_photo)
                db.session.flush()
                filepath = os.path.join(Config.UPLOAD_FOLDER, f"{new_photo.id}_{filename}")
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                new_photo.equipment_id = equipment.id
                equipment.photo = new_photo
            else:
                equipment.photo = existing_photo

        if status == 'written_off' and not WriteOff.query.filter_by(equipment_id=equipment.id).first():
            record = WriteOff(
                equipment_id=equipment.id,
                reason='Списано вручную через редактирование.',
                pdf_filename='manual_entry.pdf'
            )
            db.session.add(record)

        try:
            db.session.commit()
            flash('Оборудование успешно обновлено.', 'success')
            return redirect(url_for('equipment.view_equipment', id=id))
        except:
            db.session.rollback()
            flash('Ошибка при сохранении изменений.', 'danger')
            return redirect(url_for('equipment.edit_equipment', id=id))

    return render_template('equipment_edit.html', equipment=equipment, categories=categories)


@equipment_bp.route('/writeoff/<int:id>', methods=['GET', 'POST'])
@login_required
def writeoff_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    form = WriteOffForm()

    if form.validate_on_submit():
        file = form.pdf.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, f"writeoff_{equipment.id}_{filename}")
        file.save(filepath)

        record = WriteOff(
            equipment_id=equipment.id,
            reason=form.reason.data,
            pdf_filename=os.path.basename(filepath)
        )
        db.session.add(record)
        db.session.commit()
        flash('Оборудование успешно списано.', 'success')
        return redirect(url_for('equipment.index'))

    return render_template('writeoff.html', equipment=equipment, form=form)


@equipment_bp.route('/writeoff', methods=['GET'])
@login_required
def writeoff_list():
    records = WriteOff.query.all()
    return render_template('writeoff_list.html', records=records)

@equipment_bp.route('/writeoff/pdf/<int:id>')
@login_required
def generate_writeoff_pdf(id):
    record = WriteOff.query.get_or_404(id)
    equipment = record.equipment

    photo_path = None
    if equipment.photo:
        photo_path = os.path.abspath(
            os.path.join(Config.UPLOAD_FOLDER, f"{equipment.photo.id}_{equipment.photo.filename}")
        )

    html = render_template_string("""
        <h2>Акт списания оборудования</h2>
        <p><strong>Оборудование:</strong> {{ equipment.name }}</p>
        <p><strong>Инвентарный номер:</strong> {{ equipment.inventory_number }}</p>
        <p><strong>Категория:</strong> {{ equipment.category.name }}</p>
        <p><strong>Статус:</strong> {{ equipment.status }}</p>
        <p><strong>Дата покупки:</strong> {{ equipment.purchase_date.strftime('%d.%m.%Y') }}</p>
        <p><strong>Стоимость:</strong> {{ equipment.cost }} ₽</p>
        <p><strong>Примечание:</strong> {{ equipment.note or '—' }}</p>
        <p><strong>Дата списания:</strong> {{ record.created_at.strftime('%d.%m.%Y %H:%M') }}</p>
        <p><strong>Причина списания:</strong> {{ record.reason }}</p>

        {% if photo_path %}
        <hr>
        <p><strong>Фотография:</strong></p>
        <img src="file://{{ photo_path }}" alt="Фото" style="max-width:300px; margin-top:10px;">
        {% endif %}
    """, equipment=equipment, record=record, photo_path=photo_path)

    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=writeoff_{record.id}.pdf'
    return response
