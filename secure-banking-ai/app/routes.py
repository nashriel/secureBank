from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models.models import db, Login, Account, Transaction, Card, Upi
from datetime import datetime
import uuid

main = Blueprint('main', __name__)

# ---------------- Home Page ----------------
@main.route('/')
def index():
    return render_template('welcome.html')

# ---------------- Signup ----------------
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.signup'))

        existing_user = Login.query.filter(
            (Login.username == username) | (Login.email == email)
        ).first()
        if existing_user:
            flash('Username or email already taken.', 'danger')
            return redirect(url_for('main.signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = Login(
            fullname=fullname,
            email=email,
            username=username,
            password=hashed_password,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Create account
        account_number = str(uuid.uuid4().int)[:12]
        new_account = Account(user_id=new_user.id, account_number=account_number, balance=0.0)
        db.session.add(new_account)
        db.session.commit()

        # Create default UPI ID
        upi_id = f"{username}@bank"
        new_upi = Upi(account_id=new_account.id, upi_id=upi_id)
        db.session.add(new_upi)
        db.session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('signup.html')

# ---------------- Login ----------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Login.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

# ---------------- Dashboard ----------------
@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    user = Login.query.get(session['user_id'])

    if user.is_admin:
        all_users = Login.query.all()
        transactions = Transaction.query.all()
        return render_template(
            'dashboard.html',
            username=user.username,
            is_admin=True,
            all_users=all_users,
            transactions=transactions
        )
    else:
        account = Account.query.filter_by(user_id=user.id).first()
        deposits = Transaction.query.filter_by(user_id=user.id, txn_type='deposit').all()
        withdrawals = Transaction.query.filter_by(user_id=user.id, txn_type='withdrawal').all()
        balance = account.balance if account else 0.0
        upi = account.upi.upi_id if account and account.upi else None

        return render_template(
            'dashboard.html',
            username=user.username,
            is_admin=False,
            deposits=deposits,
            withdrawals=withdrawals,
            balance=balance,
            upi=upi
        )
# ---------------- Transactions ----------------
@main.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    account = Account.query.filter_by(user_id=user_id).first()
    balance = account.balance if account else 0.0  # Pass balance to template

    deposits = Transaction.query.filter_by(user_id=user_id, txn_type='deposit').all()
    withdrawals = Transaction.query.filter_by(user_id=user_id, txn_type='withdrawal').all()
    transfers_sent = Transaction.query.filter_by(user_id=user_id, txn_type='transfer_sent').all()
    transfers_received = Transaction.query.filter_by(user_id=user_id, txn_type='transfer_received').all()

    return render_template(
        'transactions.html',
        deposits=deposits,
        withdrawals=withdrawals,
        transfers_sent=transfers_sent,
        transfers_received=transfers_received,
        balance=balance,  # Now available in Jinja
        username=session['username']
    )
# ---------------- Admin: Users ----------------
@main.route('/users')
def users():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('main.dashboard'))

    all_users = Login.query.all()
    return render_template('users.html', users=all_users, username=session['username'])

# ---------------- Logout ----------------
@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

# ---------------- Admin Actions ----------------
@main.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = Login.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/make_admin/<int:user_id>')
def make_admin(user_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = Login.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'{user.fullname} is now an admin.', 'success')
    return redirect(url_for('main.dashboard'))

# ---------------- Transfer ----------------
@main.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    sender = Login.query.get(session['user_id'])
    sender_account = Account.query.filter_by(user_id=sender.id).first()

    if request.method == 'POST':
        recipient_account_number = request.form.get('account_number')
        recipient_upi_id = request.form.get('upi_id')
        amount = float(request.form.get('amount'))
        remarks = request.form.get('remarks', '')

        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('main.transfer'))
        if amount > sender_account.balance:
            flash('Insufficient balance!', 'danger')
            return redirect(url_for('main.transfer'))

        # Determine recipient
        recipient_account = None
        if recipient_account_number:
            recipient_account = Account.query.filter_by(account_number=recipient_account_number).first()
        elif recipient_upi_id:
            upi = Upi.query.filter_by(upi_id=recipient_upi_id).first()
            if upi:
                recipient_account = upi.account
        else:
            flash('Provide either account number or UPI ID.', 'danger')
            return redirect(url_for('main.transfer'))

        if not recipient_account:
            flash('Recipient not found!', 'danger')
            return redirect(url_for('main.transfer'))

        # Transfer
        sender_account.balance -= amount
        recipient_account.balance += amount

        txn_sender = Transaction(
            user_id=sender.id,
            account_id=sender_account.id,
            txn_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            txn_type='transfer_sent',
            amount=amount,
            date=datetime.utcnow(),
            remarks=f"To {recipient_account_number or recipient_upi_id} - {remarks}"
        )
        txn_recipient = Transaction(
            user_id=recipient_account.user_id,
            account_id=recipient_account.id,
            txn_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            txn_type='transfer_received',
            amount=amount,
            date=datetime.utcnow(),
            remarks=f"From {sender_account.account_number} - {remarks}"
        )

        db.session.add_all([sender_account, recipient_account, txn_sender, txn_recipient])
        db.session.commit()

        flash(f'Transferred ${amount} successfully!', 'success')
        return redirect(url_for('main.transfer'))

    return render_template('transfer.html', balance=sender_account.balance, username=sender.username)

import csv
from flask import Response

@main.route('/export_transactions/<string:format>')
def export_transactions(format):
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    if format == 'csv':
        def generate():
            data = csv.writer([])
            yield ','.join(['Txn ID', 'Type', 'Amount', 'Date', 'Remarks']) + '\n'
            for txn in transactions:
                row = [txn.txn_id, txn.txn_type, str(txn.amount), txn.date.strftime('%Y-%m-%d %H:%M:%S'), txn.remarks or '']
                yield ','.join(row) + '\n'

        return Response(generate(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=transactions.csv'})
    else:
        flash('Unsupported export format!', 'danger')
        return redirect(url_for('main.transactions'))
