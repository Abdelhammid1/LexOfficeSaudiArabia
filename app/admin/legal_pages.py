"""Admin editor for Terms & Privacy.

Content is stored in `system_settings` keyed by:
  - terms_html             — raw HTML for /terms
  - terms_last_updated     — Arabic display string, e.g. "1 يونيو 2026"
  - privacy_html           — raw HTML for /privacy
  - privacy_last_updated   — Arabic display string

The public templates render the DB content when set; otherwise they fall back
to the bundled static markup.
"""
from flask import render_template, request, redirect, url_for, flash, g

from app.extensions import db
from app.admin import admin_bp
from app.admin.decorators import log_action, admin_permission_required
from app.models.admin import SystemSetting


_LEGAL_KEYS = (
    'terms_html', 'terms_last_updated',
    'privacy_html', 'privacy_last_updated',
)


@admin_bp.route('/settings/legal', methods=['GET', 'POST'])
@admin_permission_required('settings', 'view', write_action='edit')
def settings_legal():
    """Edit the user-facing Terms & Conditions and Privacy Policy."""
    if request.method == 'POST':
        old_values = {k: SystemSetting.get(k, '') for k in _LEGAL_KEYS}

        for key in _LEGAL_KEYS:
            # textareas — keep raw, including newlines
            val = request.form.get(key, '')
            SystemSetting.set(key, val, admin_id=g.current_admin.id)

        log_action(
            'SETTINGS_LEGAL_UPDATED', entity_type='Setting',
            old_value=old_values,
            new_value={k: SystemSetting.get(k, '') for k in _LEGAL_KEYS},
            description='Updated Terms / Privacy content',
        )
        db.session.commit()
        flash('تم حفظ صفحات الشروط والخصوصية', 'success')
        return redirect(url_for('admin.settings_legal'))

    values = {k: (SystemSetting.get(k, '') or '') for k in _LEGAL_KEYS}
    return render_template('admin/settings/legal.html', values=values)
