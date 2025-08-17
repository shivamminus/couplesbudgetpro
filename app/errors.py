"""Error handling blueprint"""
from flask import Blueprint, render_template, request, jsonify
from app import db
import sys

bp = Blueprint('errors', __name__)

def wants_json_response():
    """Check if the client wants a JSON response"""
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

@bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if wants_json_response():
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if wants_json_response():
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if wants_json_response():
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(413)
def request_entity_too_large(error):
    """Handle file upload size errors"""
    if wants_json_response():
        return jsonify({'error': 'File too large'}), 413
    return render_template('errors/413.html'), 413
