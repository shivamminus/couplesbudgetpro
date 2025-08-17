"""Profile and partner management routes"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, PartnerRequest
from app.forms import PartnerForm, PartnerSearchForm, ProfilePictureForm, ProfileUpdateForm, ChangePasswordForm
from app.utils import save_profile_picture, delete_profile_picture
from app import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    partner_form = PartnerForm()
    profile_form = ProfileUpdateForm()
    picture_form = ProfilePictureForm()
    password_form = ChangePasswordForm()
    partner = None
    
    # Get current partner if exists
    if current_user.partner_id:
        partner = User.query.get(current_user.partner_id)
    else:
        # Check if someone has this user as their partner
        partner = User.query.filter_by(partner_id=current_user.id).first()
    
    # Handle partner linking (legacy)
    if partner_form.validate_on_submit() and 'partner_submit' in request.form:
        partner_user = User.query.filter_by(username=partner_form.partner_username.data).first()
        
        if not partner_user:
            flash('Partner username not found!', 'error')
        elif partner_user.id == current_user.id:
            flash('You cannot link yourself as a partner!', 'error')
        elif current_user.partner_id == partner_user.id:
            flash('This user is already your partner!', 'error')
        else:
            current_user.partner_id = partner_user.id
            db.session.commit()
            flash(f'Successfully linked with {partner_user.username}!', 'success')
            return redirect(url_for('profile.profile'))
    
    # Handle profile picture upload
    if picture_form.validate_on_submit() and 'picture_submit' in request.form:
        file = picture_form.profile_picture.data
        filename = save_profile_picture(file)
        
        if filename:
            # Delete old picture if not default
            old_picture = current_user.profile_picture
            if old_picture and old_picture != 'default.png':
                delete_profile_picture(old_picture)
            
            current_user.profile_picture = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Failed to upload profile picture. Please try again.', 'error')
        
        return redirect(url_for('profile.profile'))
    
    # Handle profile update
    if profile_form.validate_on_submit() and 'profile_submit' in request.form:
        # Check if username is taken (excluding current user)
        existing_user = User.query.filter(
            User.username == profile_form.username.data,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            flash('Username is already taken!', 'error')
        else:
            # Check if email is taken (excluding current user)
            existing_email = User.query.filter(
                User.email == profile_form.email.data,
                User.id != current_user.id
            ).first()
            
            if existing_email:
                flash('Email is already in use!', 'error')
            else:
                current_user.username = profile_form.username.data
                current_user.email = profile_form.email.data
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile.profile'))
    
    # Handle password change
    if password_form.validate_on_submit() and 'password_submit' in request.form:
        if not check_password_hash(current_user.password_hash, password_form.current_password.data):
            flash('Current password is incorrect!', 'error')
        elif password_form.new_password.data != password_form.confirm_password.data:
            flash('New passwords do not match!', 'error')
        else:
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile.profile'))
    
    # Pre-populate profile form with current data
    profile_form.username.data = current_user.username
    profile_form.email.data = current_user.email
    
    return render_template('profile.html', 
                         partner_form=partner_form, 
                         profile_form=profile_form,
                         picture_form=picture_form,
                         password_form=password_form,
                         partner=partner)

@profile_bp.route('/unlink_partner')
@login_required
def unlink_partner():
    """Unlink from partner"""
    current_user.partner_id = None
    db.session.commit()
    flash('Partner unlinked successfully!', 'success')
    return redirect(url_for('profile.profile'))

@profile_bp.route('/search_partners', methods=['GET', 'POST'])
@login_required
def search_partners():
    """Search for partners to link with"""
    form = PartnerSearchForm()
    users = []
    
    # Get pending requests
    pending_received = PartnerRequest.query.filter_by(
        receiver_id=current_user.id, 
        status='pending'
    ).all()
    
    pending_sent = PartnerRequest.query.filter_by(
        sender_id=current_user.id, 
        status='pending'
    ).all()
    
    if form.validate_on_submit():
        query = form.search_query.data
        users = User.query.filter(
            db.or_(
                User.username.contains(query),
                User.email.contains(query)
            ),
            User.id != current_user.id
        ).limit(10).all()
    
    return render_template('search_partners.html', 
                         form=form, 
                         users=users,
                         pending_received=pending_received,
                         pending_sent=pending_sent)

@profile_bp.route('/send_partner_request/<int:user_id>')
@login_required
def send_partner_request(user_id):
    """Send a partner request to another user"""
    target_user = User.query.get_or_404(user_id)
    
    if target_user.id == current_user.id:
        flash('You cannot send a partner request to yourself!')
        return redirect(url_for('profile.search_partners'))
    
    if current_user.partner_id or User.query.filter_by(partner_id=current_user.id).first():
        flash('You already have a partner!')
        return redirect(url_for('profile.search_partners'))
    
    # Check if request already exists
    existing_request = PartnerRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You have already sent a partner request to this user!')
        return redirect(url_for('profile.search_partners'))
    
    # Check if reverse request exists
    reverse_request = PartnerRequest.query.filter_by(
        sender_id=target_user.id,
        receiver_id=current_user.id,
        status='pending'
    ).first()
    
    if reverse_request:
        flash('This user has already sent you a partner request! Check your pending requests.')
        return redirect(url_for('profile.search_partners'))
    
    # Create new partner request
    partner_request = PartnerRequest(
        sender_id=current_user.id,
        receiver_id=target_user.id,
        message=f'{current_user.username} would like to link as financial partners.'
    )
    
    db.session.add(partner_request)
    db.session.commit()
    
    flash(f'Partner request sent to {target_user.username}!')
    return redirect(url_for('profile.search_partners'))

@profile_bp.route('/respond_partner_request/<int:request_id>/<action>')
@login_required
def respond_partner_request(request_id, action):
    """Respond to a partner request (accept/reject)"""
    partner_request = PartnerRequest.query.get_or_404(request_id)
    
    if partner_request.receiver_id != current_user.id:
        flash('You can only respond to requests sent to you!')
        return redirect(url_for('profile.search_partners'))
    
    if partner_request.status != 'pending':
        flash('This request has already been processed!')
        return redirect(url_for('profile.search_partners'))
    
    if action == 'accept':
        if current_user.partner_id or User.query.filter_by(partner_id=current_user.id).first():
            flash('You already have a partner!')
            partner_request.status = 'rejected'
        else:
            # Link the partners
            current_user.partner_id = partner_request.sender_id
            partner_request.sender.partner_id = current_user.id
            partner_request.status = 'accepted'
            
            # Cancel any other pending requests for both users
            PartnerRequest.query.filter(
                db.or_(
                    db.and_(PartnerRequest.sender_id == current_user.id, PartnerRequest.status == 'pending'),
                    db.and_(PartnerRequest.receiver_id == current_user.id, PartnerRequest.status == 'pending', PartnerRequest.id != request_id),
                    db.and_(PartnerRequest.sender_id == partner_request.sender_id, PartnerRequest.status == 'pending', PartnerRequest.id != request_id),
                    db.and_(PartnerRequest.receiver_id == partner_request.sender_id, PartnerRequest.status == 'pending')
                )
            ).update({'status': 'rejected'})
            
            flash(f'You are now linked with {partner_request.sender.username}!')
    
    elif action == 'reject':
        partner_request.status = 'rejected'
        flash(f'Partner request from {partner_request.sender.username} rejected.')
    
    db.session.commit()
    return redirect(url_for('profile.search_partners'))

@profile_bp.route('/cancel_partner_request/<int:request_id>')
@login_required
def cancel_partner_request(request_id):
    """Cancel a partner request that was sent"""
    partner_request = PartnerRequest.query.get_or_404(request_id)
    
    if partner_request.sender_id != current_user.id:
        flash('You can only cancel requests you sent!')
        return redirect(url_for('profile.search_partners'))
    
    if partner_request.status != 'pending':
        flash('This request cannot be cancelled!')
        return redirect(url_for('profile.search_partners'))
    
    db.session.delete(partner_request)
    db.session.commit()
    
    flash(f'Partner request to {partner_request.receiver.username} cancelled.')
    return redirect(url_for('profile.search_partners'))
