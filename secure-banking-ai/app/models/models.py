from datetime import datetime
from app import db   # ✅ reuse the one from __init__.py



# ---------------- User Login ----------------
class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)  # <-- Added phone
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Fixed here

    # Relationships
    accounts = db.relationship('Account', backref='owner', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)


# ---------------- Bank Account ----------------
class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    upi = db.relationship('Upi', backref='account', uselist=False)
    cards = db.relationship('Card', backref='account', lazy=True)
    transactions = db.relationship('Transaction', backref='account', lazy=True)

# ---------------- Transactions ----------------
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    txn_id = db.Column(db.String(64), unique=True, nullable=False)
    txn_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    counterparty = db.Column(db.String(120), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- UPI ----------------
class Upi(db.Model):
    __tablename__ = 'upi'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    upi_id = db.Column(db.String(120), unique=True, nullable=False)
    verified = db.Column(db.Boolean, default=False)

# ---------------- Cards ----------------
class Card(db.Model):
    __tablename__ = 'card'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    card_number = db.Column(db.String(20), unique=True)
    card_type = db.Column(db.String(20), default='debit')
    expiry = db.Column(db.String(10))
    cvv = db.Column(db.String(6))
    blocked = db.Column(db.Boolean, default=False)
    limit = db.Column(db.Float, default=5000.0)

# ---------------- Subscriptions ----------------
class Subscription(db.Model):
    __tablename__ = 'subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_billing_date = db.Column(db.DateTime, nullable=True)
    last_billed_date = db.Column(db.DateTime, nullable=True)

    