from datetime import datetime

from flask import Blueprint, flash, session, render_template, redirect, url_for

from flaskr.models import Capsule, User


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    public_capsules = Capsule.query.filter_by(is_public=True).order_by(Capsule.unlock_date).limit(5).all()
    unlocked_public = [c for c in public_capsules if c.unlock_date <= datetime.utcnow()]
    locked_public = [c for c in public_capsules if c.unlock_date > datetime.utcnow()]

    return render_template('index.html',
                           now = datetime.utcnow(),
                           unlocked_capsules=unlocked_public,
                           locked_capsules=locked_public)


@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access your dashboard')
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    current_time = datetime.utcnow()

    unlocked_capsules = [c for c in user.capsules if c.unlock_date <= current_time]
    locked_capsules = [c for c in user.capsules if c.unlock_date > current_time]

    return render_template('dashboard.html',
                           now = datetime.utcnow(),
                           user=user,
                           unlocked_capsules=unlocked_capsules,
                           locked_capsules=locked_capsules)

