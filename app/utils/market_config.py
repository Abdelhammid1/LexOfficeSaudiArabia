"""Per-market configuration: currency, phone format, bar body label, plan comparison rows.

The platform is configured for the Saudi market only. The historical 'eg' /
multi-market plumbing remains in place so that downstream code (tenant.market,
g.market) keeps working without modification — it just always resolves to 'sa'.
"""

DEFAULT_MARKET = 'sa'
SUPPORTED_MARKETS = ('sa',)


MARKET_CONFIG = {
    'sa': {
        'code': 'sa',
        'country_code_iso': 'SA',
        'name_ar': 'المملكة العربية السعودية',
        'name_en': 'Saudi Arabia',
        'currency_code': 'SAR',
        'currency_symbol_ar': 'ر.س',
        # Saudi mobile: 05XXXXXXXX (10 digits) — also accept +9665XXXXXXXX form
        # after normalization which strips the prefix.
        'phone_regex': r'^05\d{8}$',
        'phone_placeholder': '05xxxxxxxx',
        'phone_country_prefix': '+966',
        'bar_body_ar': 'الهيئة السعودية للمحامين',
        'bar_registration_label_ar': 'رقم القيد بالهيئة',
        'timezone': 'Asia/Riyadh',
        'governorate_label_ar': 'المنطقة',
    },
}


# Plan comparison table rows. Each row shows up as one line in the
# choose_plan.html pricing matrix. Plans store a dict at
# subscription_plans.comparison keyed by `key`. Order here = display order.
PLAN_COMPARISON_ROWS = [
    {'key': 'users',           'label_ar': 'المستخدمين (المحامين)'},
    {'key': 'cases',           'label_ar': 'إدارة القضايا والجلسات'},
    {'key': 'storage',         'label_ar': 'التخزين السحابي'},
    {'key': 'clients_poa',     'label_ar': 'إدارة الموكلين والتوكيلات'},
    {'key': 'calendar',        'label_ar': 'الأجندة والتقويم الرقمي'},
    {'key': 'tasks',           'label_ar': 'إدارة المهام (Tasks)'},
    {'key': 'judgments',       'label_ar': 'سجل الأحكام والاستئناف'},
    {'key': 'enforcement',     'label_ar': 'متابعة التنفيذ'},
    {'key': 'finance',         'label_ar': 'النظام المالي (إيصالات/فواتير)'},
    {'key': 'expenses',        'label_ar': 'إدارة المصاريف والأتعاب'},
    {'key': 'templates',       'label_ar': 'النماذج القانونية الجاهزة'},
    {'key': 'notifications',   'label_ar': 'قنوات التنبيهات'},
    {'key': 'ai',              'label_ar': 'الذكاء الاصطناعي (AI)'},
    {'key': 'dashboard',       'label_ar': 'لوحة التحكم (Dashboard)'},
    {'key': 'reports',         'label_ar': 'التقارير والتحليلات'},
    {'key': 'support',         'label_ar': 'الدعم الفني'},
    {'key': 'hosting',         'label_ar': 'الاستضافة'},
    {'key': 'api',             'label_ar': 'الربط التقني (API)'},
]


def normalize_market(value):
    """Coerce any input to the supported market. Single-market deployment, so
    always returns 'sa' — but the signature stays put so downstream callers
    don't need to change."""
    return DEFAULT_MARKET


def get_config(market):
    """Return the config dict for a market. Always SA in this deployment."""
    return MARKET_CONFIG[DEFAULT_MARKET]
