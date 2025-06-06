from app import db
from flask_login import UserMixin
from datetime import datetime

# ENUM-статусы
STATUSES = ('in_use', 'under_repair', 'written_off')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)


class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    inventory_number = db.Column(db.String(100), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(*STATUSES, name='status_enum'), nullable=False)
    note = db.Column(db.Text)

    category = db.relationship('Category', backref='equipments')
    photo = db.relationship('Photo', uselist=False, backref='equipment')
    maintenance_records = db.relationship('Maintenance', backref='equipment', cascade="all, delete")
    persons = db.relationship('Person', secondary='equipment_person', backref='equipments')


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(50), nullable=False)
    md5_hash = db.Column(db.String(32), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)



class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    type = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text)


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(150))


# Связующая таблица: Equipment ↔ Person
equipment_person = db.Table('equipment_person',
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE')),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id', ondelete='CASCADE'))
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    role = db.relationship('Role')
