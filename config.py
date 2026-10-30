import os

# Automatically load .env file if present
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, 'r', encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'expense_tracker.db')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days in seconds
