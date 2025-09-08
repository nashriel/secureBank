from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models.models import db, Login, Account, Transaction, Card, Upi, Subscription
from datetime import datetime, timezone, timedelta
import uuid

main = Blueprint('main', __name__)

# ---------------- Home ----------------
@main.route('/')
def index_view():
    return render_template('welcome.html')

# ---------------- Signup ----------------
@main.route('/signup', methods=['GET', 'POST'])
def signup_view():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.signup_view'))

        existing_user = Login.query.filter((Login.username==username)|(Login.email==email)).first()
        if existing_user:
            flash('Username or email already taken.', 'danger')
            return redirect(url_for('main.signup_view'))

        hashed_password = generate_password_hash(password)
        new_user = Login(fullname=fullname, email=email, username=username,
                         phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Create default account
        account_number = str(uuid.uuid4().int)[:12]
        account = Account(user_id=new_user.id, account_number=account_number)
        db.session.add(account)
        db.session.commit()

        # Default UPI
        upi = Upi(account_id=account.id, upi_id=f"{username}@bank")
        db.session.add(upi)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('main.login_view'))

    return render_template('signup.html')


# ---------------- Login ----------------
@main.route('/login', methods=['GET','POST'])
def login_view():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        user = Login.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            session['user_id']=user.id
            session['username']=user.username
            session['is_admin']=user.is_admin
            flash('Logged in successfully!','success')
            return redirect(url_for('main.dashboard_view'))
        flash('Invalid username or password','danger')
        return redirect(url_for('main.login_view'))
    return render_template('login.html')


# ---------------- Logout ----------------
@main.route('/logout')
def logout_view():
    session.clear()
    flash('Logged out successfully.','info')
    return redirect(url_for('main.index_view'))


# ---------------- Dashboard ----------------
@main.route('/dashboard')
def dashboard_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))
    
    user = Login.query.get(session['user_id'])
    account = Account.query.filter_by(user_id=user.id).first()
    balance = account.balance if account else 0.0

    if user.is_admin:
        all_users = Login.query.all()
        user_details = []
        for u in all_users:
            primary_account = u.accounts[0] if u.accounts else None
            user_details.append({
                "id": u.id,
                "fullname": u.fullname,
                "email": u.email,
                "username": u.username,
                "phone": u.phone or "N/A",
                "account_number": primary_account.account_number if primary_account else "N/A",
                "balance": primary_account.balance if primary_account else 0.0,
                "num_cards": len(primary_account.cards) if primary_account else 0,
                "num_subscriptions": len(u.subscriptions),
                "is_admin": u.is_admin
            })

        return render_template(
            'dashboard.html',
            username=user.fullname.upper(),
            is_admin=True,
            all_users=user_details
        )

    deposits = Transaction.query.filter_by(user_id=user.id, txn_type='deposit').all()
    withdrawals = Transaction.query.filter_by(user_id=user.id, txn_type='withdrawal').all()
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    cards = Card.query.filter_by(account_id=account.id).all() if account else []
    upis = Upi.query.filter_by(account_id=account.id).all() if account else []

    return render_template(
        'dashboard.html',
        username=user.fullname.upper(),
        is_admin=False,
        user=user,
        account=account,
        deposits=deposits,
        withdrawals=withdrawals,
        balance=balance,
        subscriptions=subscriptions,
        cards=cards,
        upis=upis
    )


# ---------------- Transactions ----------------
@main.route('/transactions')
def transactions_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    user_id = session['user_id']
    account = Account.query.filter_by(user_id=user_id).first()
    balance = account.balance if account else 0.0

    deposits = Transaction.query.filter_by(user_id=user_id, txn_type='deposit').all()
    withdrawals = Transaction.query.filter_by(user_id=user_id, txn_type='withdrawal').all()
    transfers_sent = Transaction.query.filter_by(user_id=user_id, txn_type='transfer_sent').all()
    transfers_received = Transaction.query.filter_by(user_id=user_id, txn_type='transfer_received').all()

    return render_template('transactions.html',
                           deposits=deposits,
                           withdrawals=withdrawals,
                           transfers_sent=transfers_sent,
                           transfers_received=transfers_received,
                           balance=balance,
                           username=session['username'])


# ---------------- Transfer ----------------
@main.route('/transfer', methods=['GET','POST'])
def transfer_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    sender = Login.query.get(session['user_id'])
    sender_account = Account.query.filter_by(user_id=sender.id).first()

    if request.method=='POST':
        recipient_account_number = request.form.get('account_number')
        recipient_upi_id = request.form.get('upi_id')
        amount = float(request.form.get('amount'))
        remarks = request.form.get('remarks', '')

        if amount <=0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('main.transfer_view'))
        if amount>sender_account.balance:
            flash('Insufficient balance!', 'danger')
            return redirect(url_for('main.transfer_view'))

        recipient_account = None
        if recipient_account_number:
            recipient_account = Account.query.filter_by(account_number=recipient_account_number).first()
        elif recipient_upi_id:
            upi = Upi.query.filter_by(upi_id=recipient_upi_id).first()
            if upi:
                recipient_account = upi.account

        if not recipient_account:
            flash('Recipient not found!', 'danger')
            return redirect(url_for('main.transfer_view'))

        sender_account.balance -= amount
        recipient_account.balance += amount
        now = datetime.now(timezone.utc)

        txn_sender = Transaction(
            user_id=sender.id,
            account_id=sender_account.id,
            txn_id=f"TXN{uuid.uuid4().hex[:12]}",
            txn_type='transfer_sent',
            amount=amount,
            remarks=f"To {recipient_account_number or recipient_upi_id} - {remarks}",
            date=now
        )
        txn_recipient = Transaction(
            user_id=recipient_account.user_id,
            account_id=recipient_account.id,
            txn_id=f"TXN{uuid.uuid4().hex[:12]}",
            txn_type='transfer_received',
            amount=amount,
            remarks=f"From {sender_account.account_number} - {remarks}",
            date=now
        )

        db.session.add_all([sender_account, recipient_account, txn_sender, txn_recipient])
        db.session.commit()

        flash(f'Transferred ${amount} successfully!', 'success')
        return redirect(url_for('main.transfer_view'))

    return render_template('transfer.html', balance=sender_account.balance, username=sender.username)


# ---------------- Subscription ----------------
@main.route('/subscription', methods=['GET','POST'])
def subscription_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name')
        amount = float(request.form.get('amount'))
        frequency = request.form.get('frequency')

        now = datetime.utcnow()
        if frequency == 'Weekly':
            next_billing = now + timedelta(weeks=1)
        elif frequency == 'Monthly':
            next_billing = now + timedelta(days=30)
        elif frequency == 'Yearly':
            next_billing = now + timedelta(days=365)
        else:
            next_billing = None

        new_sub = Subscription(
            user_id=user_id,
            name=name,
            amount=amount,
            frequency=frequency,
            active=True,
            created_at=now,
            next_billing_date=next_billing
        )
        db.session.add(new_sub)
        db.session.commit()
        flash('Subscription added successfully!', 'success')
        return redirect(url_for('main.subscription_view'))

    subs = Subscription.query.filter_by(user_id=user_id).all()
    return render_template('subscription.html', subscriptions=subs, username=session['username'])


@main.route('/subscription/delete/<int:sub_id>')
def delete_subscription_view(sub_id):
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    sub = Subscription.query.get_or_404(sub_id)
    if sub.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.subscription_view'))

    db.session.delete(sub)
    db.session.commit()
    flash('Subscription cancelled successfully.', 'success')
    return redirect(url_for('main.subscription_view'))


# ---------------- Admin ----------------
@main.route('/delete_user/<int:user_id>')
def delete_user_view(user_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard_view'))
    user = Login.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('main.dashboard_view'))


@main.route('/make_admin/<int:user_id>')
def make_admin_view(user_id):
    if not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard_view'))
    user = Login.query.get_or_404(user_id)
    user.is_admin=True
    db.session.commit()
    flash(f'{user.fullname} is now an admin.', 'success')
    return redirect(url_for('main.dashboard_view'))



# ---------------- Card Management ----------------
# ---------------- Card Management ----------------
@main.route('/cards')
def cards_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))
    
    account = Account.query.filter_by(user_id=session['user_id']).first()
    cards = Card.query.filter_by(account_id=account.id).all() if account else []
    return render_template('cards.html', cards=cards, username=session['username'])


@main.route('/cards/add', methods=['POST'])
def add_card_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    account = Account.query.filter_by(user_id=session['user_id']).first()
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('main.cards_view'))

    card_type = request.form.get('card_type')
    card_number = request.form.get('card_number').strip()
    expiry = request.form.get('expiry_date')
    pin = request.form.get('pin')

    # Basic validations
    if not card_number.isdigit() or len(card_number) != 16:
        flash('Card number must be 16 digits!', 'danger')
        return redirect(url_for('main.cards_view'))
    if not pin.isdigit() or len(pin) != 4:
        flash('PIN must be 4 digits!', 'danger')
        return redirect(url_for('main.cards_view'))

    cvv = str(uuid.uuid4().int)[:3]
    hashed_pin = generate_password_hash(pin)

    new_card = Card(
        account_id=account.id,
        card_number=card_number,
        card_type=card_type,
        expiry=expiry,
        cvv=cvv,
        pin=hashed_pin
    )
    db.session.add(new_card)
    db.session.commit()
    flash(f'{card_type.capitalize()} card added successfully!', 'success')
    return redirect(url_for('main.cards_view'))


@main.route('/cards/set_pin/<int:card_id>', methods=['POST'])
def set_pin_view(card_id):
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    card = Card.query.get_or_404(card_id)
    account = Account.query.filter_by(user_id=session['user_id']).first()
    if card.account_id != account.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.cards_view'))

    new_pin = request.form.get('pin')
    if not new_pin.isdigit() or len(new_pin) != 4:
        flash('PIN must be 4 digits!', 'danger')
        return redirect(url_for('main.cards_view'))
    card.pin = generate_password_hash(new_pin)
    db.session.commit()
    flash('PIN updated successfully!', 'success')
    return redirect(url_for('main.cards_view'))


@main.route('/cards/delete/<int:card_id>')
def delete_card_view(card_id):
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    card = Card.query.get_or_404(card_id)
    account = Account.query.filter_by(user_id=session['user_id']).first()
    if card.account_id != account.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.cards_view'))

    db.session.delete(card)
    db.session.commit()
    flash('Card deleted successfully.', 'success')
    return redirect(url_for('main.cards_view'))


@main.route('/cards/toggle/<int:card_id>')
def toggle_card_view(card_id):
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    card = Card.query.get_or_404(card_id)
    account = Account.query.filter_by(user_id=session['user_id']).first()
    if card.account_id != account.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.cards_view'))

    card.blocked = not card.blocked
    db.session.commit()
    status = 'unblocked' if not card.blocked else 'blocked'
    flash(f'Card {status} successfully.', 'success')
    return redirect(url_for('main.cards_view'))

# ---------------- Deposit ----------------
@main.route('/deposit', methods=['GET','POST'])
def deposit_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    user = Login.query.get(session['user_id'])
    account = Account.query.filter_by(user_id=user.id).first()
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('main.dashboard_view'))

    if request.method=='POST':
        try:
            amount = float(request.form.get('amount'))
            remarks = request.form.get('remarks','')
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('main.deposit_view'))

        if amount <=0:
            flash('Amount must be > 0', 'danger')
            return redirect(url_for('main.deposit_view'))

        account.balance += amount
        now = datetime.now(timezone.utc)

        txn = Transaction(
            user_id=user.id,
            account_id=account.id,
            txn_id=f"TXN{uuid.uuid4().hex[:12]}",
            txn_type='deposit',
            amount=amount,
            remarks=remarks,
            date=now
        )
        db.session.add(account)
        db.session.add(txn)
        db.session.commit()

        flash(f'Deposited ${amount} successfully!', 'success')
        return redirect(url_for('main.deposit_view'))

    return render_template('deposit.html', balance=account.balance, username=user.username)


# ---------------- Withdrawal ----------------
@main.route('/withdraw', methods=['GET','POST'])
def withdrawal_view():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('main.login_view'))

    user = Login.query.get(session['user_id'])
    account = Account.query.filter_by(user_id=user.id).first()
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('main.dashboard_view'))

    if request.method=='POST':
        try:
            amount = float(request.form.get('amount'))
            remarks = request.form.get('remarks','')
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('main.withdrawal_view'))

        if amount <=0:
            flash('Amount must be > 0', 'danger')
            return redirect(url_for('main.withdrawal_view'))
        if amount > account.balance:
            flash('Insufficient balance!', 'danger')
            return redirect(url_for('main.withdrawal_view'))

        account.balance -= amount
        now = datetime.now(timezone.utc)

        txn = Transaction(
            user_id=user.id,
            account_id=account.id,
            txn_id=f"TXN{uuid.uuid4().hex[:12]}",
            txn_type='withdrawal',
            amount=amount,
            remarks=remarks,
            date=now
        )
        db.session.add(account)
        db.session.add(txn)
        db.session.commit()

        flash(f'Withdrawn ${amount} successfully!', 'success')
        return redirect(url_for('main.withdrawal_view'))

    return render_template('withdrawal.html', balance=account.balance, username=user.username)
