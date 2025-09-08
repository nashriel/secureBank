import re
import uuid
from functools import wraps
from flask import session, redirect, url_for, flash

ACCOUNT_LEN = 12

def generate_account_number():
    # 12-digit pseudo-random number; guarantee first digit non-zero
    return str(uuid.uuid4().int)[0:ACCOUNT_LEN].rjust(ACCOUNT_LEN, '1')

def generate_txn_id():
    return uuid.uuid4().hex[:16]

def generate_upi_id(username: str, bank_slug="bank"):
    return f"{username}@{bank_slug}"

def validate_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", phone or ""))

def validate_aadhaar(aadhaar: str) -> bool:
    return bool(re.fullmatch(r"\d{12}", aadhaar or ""))

def validate_password(pw: str) -> bool:
    if not pw or len(pw) < 8: return False
    return (re.search(r"[A-Z]", pw) and
            re.search(r"[a-z]", pw) and
            re.search(r"\d", pw) and
            re.search(r"[^\w\s]", pw))

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not (session.get('user_id') and session.get('is_admin')):
            flash('Access denied. Admins only!', 'danger')
            return redirect(url_for('banking.dashboard'))
        return f(*args, **kwargs)
    return wrapper
