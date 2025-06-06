from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

class MaintenanceForm(FlaskForm):
    date = DateField('Дата обслуживания', validators=[DataRequired()])
    type = StringField('Тип обслуживания', validators=[DataRequired()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Добавить')

class WriteOffForm(FlaskForm):
    reason = TextAreaField('Причина списания', validators=[DataRequired()])
    pdf = FileField('Акт списания (PDF)', validators=[FileAllowed(['pdf'], 'Только PDF-файлы!')])
    submit = SubmitField('Списать')