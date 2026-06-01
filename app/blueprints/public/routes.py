"""Public-facing legal pages (no auth required).

Required by App Store / Play Store policies:
- /terms       Terms of Service
- /privacy     Privacy Policy
- /account/delete  Public account deletion page (Google Play requirement)

Terms / Privacy content is pulled from SystemSetting (admin-editable). When the
DB value is empty, the templates fall back to their bundled static copy.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for

from app.extensions import db
from app.models.user import User
from app.models.admin import SystemSetting

public_bp = Blueprint('public', __name__)


def _legal_context(prefix):
    """Pull HTML + last-updated string for either 'terms' or 'privacy'."""
    return {
        'custom_html': (SystemSetting.get(f'{prefix}_html', '') or '').strip(),
        'last_updated': (SystemSetting.get(f'{prefix}_last_updated', '') or '').strip(),
    }


@public_bp.route('/terms')
def terms():
    return render_template('public/terms.html', **_legal_context('terms'))


@public_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html', **_legal_context('privacy'))


@public_bp.route('/account/delete', methods=['GET', 'POST'])
def account_delete():
    """Public web flow for account deletion (no auth needed before action).

    User enters email + password. If valid, mark account for deletion (90-day
    grace period). They can cancel by logging back in to the app within 90 days.
    """
    if request.method == 'GET':
        return render_template('public/account_delete.html')

    email = (request.form.get('email') or '').strip().lower()
    password = (request.form.get('password') or '').strip()
    reason = (request.form.get('reason') or '').strip() or None

    if not email or not password:
        flash('البريد الإلكتروني وكلمة المرور مطلوبان', 'error')
        return render_template('public/account_delete.html')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('بيانات الدخول غير صحيحة', 'error')
        return render_template('public/account_delete.html')

    if user.deletion_scheduled_at:
        final_at = user.deletion_scheduled_at + timedelta(days=90)
        return render_template(
            'public/account_delete_success.html',
            final_at=final_at,
            scheduled_at=user.deletion_scheduled_at,
            already=True,
        )

    user.deletion_scheduled_at = datetime.utcnow()
    user.deletion_reason = reason
    db.session.commit()

    final_at = user.deletion_scheduled_at + timedelta(days=90)
    return render_template(
        'public/account_delete_success.html',
        final_at=final_at,
        scheduled_at=user.deletion_scheduled_at,
        already=False,
    )
