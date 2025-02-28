from datetime import datetime
import os
import secrets
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename


from flaskr import db, config
from flaskr.models import Capsule, CapsuleItem


bp = Blueprint('capsule', __name__)


@bp.route('/create_capsule', methods=['GET', 'POST'])
def create_capsule():
    if 'user_id' not in session:
        flash('Please log in to create a time capsule')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        unlock_date_str = request.form.get('unlock_date')
        is_public = True if request.form.get('is_public') else False

        try:
            unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')
            if unlock_date <= datetime.utcnow():
                flash('Unlock date must be in the future')
                return redirect(url_for('capsule.create_capsule'))

            # Generate a unique access code
            access_code = secrets.token_hex(5)

            capsule = Capsule(
                title=title,
                description=description,
                unlock_date=unlock_date,
                user_id=session['user_id'],
                is_public=is_public,
                access_code=access_code
            )

            db.session.add(capsule)
            db.session.commit()

            flash('Time capsule created successfully!')
            return redirect(url_for('capsule.edit_capsule', capsule_id=capsule.id))

        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('capsule.create_capsule'))

    return render_template('create_capsule.html')


@bp.route('/capsule/<capsule_id>')
def view_capsule(capsule_id):
    capsule = Capsule.query.get_or_404(capsule_id)
    current_time = datetime.utcnow()

    # Check if capsule is unlocked or belongs to current user
    is_owner = 'user_id' in session and capsule.user_id == session['user_id']
    is_unlocked = capsule.unlock_date <= current_time

    if not (is_owner or (is_unlocked and capsule.is_public)):
        # If it's locked and not the owner, check if access code is provided
        access_code = request.args.get('access_code')
        if not access_code or access_code != capsule.access_code:
            flash('This time capsule is still locked or you do not have permission to view it')
            return redirect(url_for('main.index'))

    # Sort items by type
    text_items = [item for item in capsule.items if item.type == 'text']
    file_items = [item for item in capsule.items if item.type != 'text']

    return render_template('view_capsule.html',
                           capsule=capsule,
                           text_items=text_items,
                           file_items=file_items,
                           now = datetime.utcnow(),
                           is_owner=is_owner,
                           is_unlocked=is_unlocked)


@bp.route('/capsule/<capsule_id>/edit', methods=['GET', 'POST'])
def edit_capsule(capsule_id):
    if 'user_id' not in session:
        flash('Please log in')
        return redirect(url_for('auth.login'))

    capsule = Capsule.query.get_or_404(capsule_id)

    # Ensure only the owner can edit
    if capsule.user_id != session['user_id']:
        flash('You do not have permission to edit this capsule')
        return redirect(url_for('main.dashboard'))

    # Check if the capsule is already unlocked
    if capsule.unlock_date <= datetime.utcnow():
        flash('This capsule has already been unlocked and cannot be edited')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule.id))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_text':
            content = request.form.get('content')
            if content:
                item = CapsuleItem(type='text', content=content, capsule_id=capsule.id)
                db.session.add(item)
                db.session.commit()
                flash('Text added to time capsule')

        elif action == 'add_file':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file:
                filename = secure_filename(file.filename)
                # Create a unique filename with UUID
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
                file.save(file_path)

                # Determine file type
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    item_type = 'image'
                elif file_ext in ['.mp3', '.wav', '.ogg']:
                    item_type = 'audio'
                else:
                    item_type = 'file'

                item = CapsuleItem(
                    type=item_type,
                    file_path=file_path,
                    file_name=filename,
                    capsule_id=capsule.id
                )
                db.session.add(item)
                db.session.commit()
                flash('File added to time capsule')

        elif action == 'update_capsule':
            title = request.form.get('title')
            description = request.form.get('description')
            unlock_date_str = request.form.get('unlock_date')
            is_public = True if request.form.get('is_public') else False

            try:
                unlock_date = datetime.strptime(unlock_date_str, '%Y-%m-%d')
                if unlock_date <= datetime.utcnow():
                    flash('Unlock date must be in the future')
                else:
                    capsule.title = title
                    capsule.description = description
                    capsule.unlock_date = unlock_date
                    capsule.is_public = is_public
                    db.session.commit()
                    flash('Capsule updated successfully')
            except ValueError:
                flash('Invalid date format')

    # Sort items by type
    text_items = [item for item in capsule.items if item.type == 'text']
    file_items = [item for item in capsule.items if item.type != 'text']

    return render_template('edit_capsule.html',
                           capsule=capsule,
                           text_items=text_items,
                           file_items=file_items)


@bp.route('/capsule/<capsule_id>/delete')
def delete_capsule(capsule_id):
    if 'user_id' not in session:
        flash('Please log in')
        return redirect(url_for('auth.login'))

    capsule = Capsule.query.get_or_404(capsule_id)

    # Ensure only the owner can delete
    if capsule.user_id != session['user_id']:
        flash('You do not have permission to delete this capsule')
        return redirect(url_for('main.dashboard'))

    # Delete any associated files first
    for item in capsule.items:
        if item.file_path and os.path.exists(item.file_path):
            os.remove(item.file_path)

    db.session.delete(capsule)
    db.session.commit()

    flash('Time capsule deleted successfully')
    return redirect(url_for('main.dashboard'))


@bp.route('/item/<item_id>/delete')
def delete_item(item_id):
    if 'user_id' not in session:
        flash('Please log in')
        return redirect(url_for('auth.login'))

    item = CapsuleItem.query.get_or_404(item_id)
    capsule = item.capsule

    # Ensure only the owner can delete
    if capsule.user_id != session['user_id']:
        flash('You do not have permission to delete this item')
        return redirect(url_for('main.dashboard'))

    # Check if the capsule is already unlocked
    if capsule.unlock_date <= datetime.utcnow():
        flash('This capsule has already been unlocked and items cannot be deleted')
        return redirect(url_for('capsule.view_capsule', capsule_id=capsule.id))

    # Delete the file if it exists
    if item.file_path and os.path.exists(item.file_path):
        os.remove(item.file_path)

    db.session.delete(item)
    db.session.commit()

    flash('Item deleted from time capsule')
    return redirect(url_for('capsule.edit_capsule', capsule_id=capsule.id))


@bp.route('/download/<item_id>')
def download_file(item_id):
    item = CapsuleItem.query.get_or_404(item_id)
    capsule = item.capsule

    # Check if the user has permission to download
    is_owner = 'user_id' in session and capsule.user_id == session['user_id']
    is_unlocked = capsule.unlock_date <= datetime.utcnow()

    if not (is_owner or (is_unlocked and capsule.is_public)):
        # If it's locked and not the owner, check if access code is provided
        access_code = request.args.get('access_code')
        if not access_code or access_code != capsule.access_code:
            flash('You do not have permission to download this file')
            return redirect(url_for('main.index'))

    return send_file(item.file_path, as_attachment=True, download_name=item.file_name)


@bp.route('/access_capsule', methods=['GET', 'POST'])
def access_capsule():
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        capsule = Capsule.query.filter_by(access_code=access_code).first()

        if capsule:
            return redirect(url_for('capsule.view_capsule', capsule_id=capsule.id, access_code=access_code))
        else:
            flash('Invalid access code')

    return render_template('access_capsule.html')