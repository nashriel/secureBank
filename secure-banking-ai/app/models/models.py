from datetime import datetime
from app import db   # use the single db instance created in __init__.py


class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    dob = db.Column(db.String(20))
    aadhaar = db.Column(db.String(12))
    pan = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    accounts = db.relationship('Account', backref='owner', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)


class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    upi = db.relationship('Upi', backref='account', uselist=False)
    card = db.relationship('Card', backref='account', uselist=False)
    transactions = db.relationship('Transaction', backref='account', lazy=True)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    txn_id = db.Column(db.String(64), unique=True, nullable=False)
    txn_type = db.Column(db.String(20), nullable=False)  # deposit / withdrawal / transfer
    amount = db.Column(db.Float, nullable=False)
    counterparty = db.Column(db.String(120), nullable=True)  # UPI id or account number
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def date(self):
        return self.created_at



class Upi(db.Model):
    __tablename__ = 'upi'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    upi_id = db.Column(db.String(120), unique=True, nullable=False)
    verified = db.Column(db.Boolean, default=False)


class Card(db.Model):
    __tablename__ = 'card'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    card_number = db.Column(db.String(20), unique=True)
    expiry = db.Column(db.String(10))
    cvv = db.Column(db.String(6))
    blocked = db.Column(db.Boolean, default=False)
    limit = db.Column(db.Float, default=5000.0)
