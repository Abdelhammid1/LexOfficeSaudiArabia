"""Market resolution — single-market deployment (KSA only).

This module previously supported per-request market detection via cookie,
Cloudflare header, GeoIP DB, and Accept-Language sniffing. The platform is
now configured exclusively for Saudi Arabia, so detection collapses to a
constant 'sa'. The before/after-request hooks are kept as no-ops so that
downstream code reading `g.market` continues to work without modification.
"""
from flask import g, request

from app.utils.market_config import DEFAULT_MARKET


COOKIE_NAME = 'lex_market'


def detect_market():
    """Always returns the single supported market."""
    return DEFAULT_MARKET


def install_market_hook(app):
    """Pin g.market = 'sa' on every request. Idempotent."""

    @app.before_request
    def _resolve_market():  # noqa: F811
        if request.endpoint in ('static',) or request.path.startswith('/static/'):
            return
        g.market = DEFAULT_MARKET


def current_market():
    """Helper for code that needs the market without importing g everywhere."""
    return DEFAULT_MARKET
