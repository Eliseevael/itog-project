from flask import Blueprint, render_template
from flask_login import login_required, current_user

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/')
@login_required
def index():
    return render_template('equipment_list.html')
