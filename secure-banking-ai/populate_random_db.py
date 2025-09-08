import random
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.models import Login, Account, Transaction, Upi, Card

# ------------------- Flask app context -------------------
app = create_app()
with app.app_context():

    # Clear previous data
    db.drop_all()
    db.create_all()
    print("Database reset. Tables created!")

    # ------------------- Users -------------------
    users_data = [
        ("Alice Smith", "alice@example.com", "alice", "alice123"),
        ("Bob Smith", "bob@example.com", "bob", "bob123"),
        ("Charlie Smith", "charlie@example.com", "charlie", "charlie123"),
        ("David Smith", "david@example.com", "david", "david123"),
        ("Eve Smith", "eve@example.com", "eve", "eve123"),
        ("Admin User", "admin@gmail.com", "admin", "admin123")
    ]

    users = []
    for fullname, email, username, password in users_data:
        user = Login(
            fullname=fullname,
            email=email,
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            is_admin=(username == "admin")
        )
        db.session.add(user)
        users.append(user)

    db.session.commit()
    print("Users added!")

    # ------------------- Accounts -------------------
    accounts = []
    for user in users:
        account = Account(
            user_id=user.id,
            account_number=f"AC{random.randint(10000000, 99999999)}",
            balance=0.0  # start with zero balance
        )
        db.session.add(account)
        accounts.append(account)
    db.session.commit()
    print("Accounts added!")

    # ------------------- Transactions (Deposits & Withdrawals) -------------------
    for account in accounts:
        for _ in range(random.randint(5, 10)):
            txn_type = random.choice(["deposit", "withdrawal"])
            amount = round(random.uniform(50, 1000), 2)

            # Prevent negative balance
            if txn_type == "withdrawal" and account.balance < amount:
                txn_type = "deposit"

            txn_created_at = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            txn = Transaction(
                user_id=account.user_id,
                account_id=account.id,
                txn_id=f"TXN{random.randint(1000000, 9999999)}",
                txn_type=txn_type,
                amount=amount,
                counterparty=None,
                remarks=random.choice(["Payment", "Bill", "Salary"]),
                created_at=txn_created_at
            )
            db.session.add(txn)

            # Update balance
            if txn_type == "deposit":
                account.balance += amount
            else:
                account.balance -= amount
    db.session.commit()
    print("Deposits and withdrawals added!")

    # ------------------- Transfers Between Accounts -------------------
    for _ in range(random.randint(5, 10)):
        sender, receiver = random.sample(accounts, 2)
        amount = round(random.uniform(20, sender.balance), 2) if sender.balance > 20 else 0
        if amount > 0:
            sender.balance -= amount
            receiver.balance += amount

            transfer_time = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            txn_sender = Transaction(
                user_id=sender.user_id,
                account_id=sender.id,
                txn_id=f"TXN{random.randint(1000000, 9999999)}",
                txn_type="transfer",
                amount=amount,
                counterparty=receiver.account_number,
                remarks="Transfer to another account",
                created_at=transfer_time
            )
            txn_receiver = Transaction(
                user_id=receiver.user_id,
                account_id=receiver.id,
                txn_id=f"TXN{random.randint(1000000, 9999999)}",
                txn_type="transfer",
                amount=amount,
                counterparty=sender.account_number,
                remarks="Received from another account",
                created_at=transfer_time
            )
            db.session.add(txn_sender)
            db.session.add(txn_receiver)

    db.session.commit()
    print("Random transfers added!")

    # ------------------- UPI -------------------
    for account in accounts:
        upi = Upi(
            account_id=account.id,
            upi_id=f"{account.user_id}_{random.randint(1000,9999)}@bank",
            verified=random.choice([True, False])
        )
        db.session.add(upi)
    db.session.commit()
    print("UPIs added!")

    # ------------------- Cards -------------------
    for account in accounts:
        card = Card(
            account_id=account.id,
            card_number=f"{random.randint(4000000000000000, 4999999999999999)}",
            expiry=f"{random.randint(1,12):02d}/{random.randint(25,30)}",
            cvv=f"{random.randint(100,999)}",
            blocked=random.choice([True, False]),
            limit=round(random.uniform(1000, 10000), 2)
        )
        db.session.add(card)
    db.session.commit()
    print("Cards added!")

    print("Database populated successfully with timezone-aware historical transactions!")
