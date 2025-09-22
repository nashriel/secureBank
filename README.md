# Secure Online Banking System with AI-Based Fraud Detection

A modern web-based online banking system built with **Python, Flask, and Machine Learning** to ensure secure transactions and detect fraud in real-time.

---

##  Key Features

-  User registration and login with hashed passwords
-  Fraud detection using a trained ML model (Random Forest/XGBoost)
-  Money transfers with real-time fraud risk scoring
-  Transaction dashboards with interactive charts
-  Downloadable transaction reports in PDF format
-  Admin panel to view users and monitor fraud alerts
-  Optional email/SMS notifications via Flask-Mail/Twilio

---

##  Project Structure

```bash
secure-banking-ai/
├── README.md
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── reset_db.py
│   ├── utils.py
│   ├── ml/
│   │   └── fraud_detector.pkl
│   ├── models/
│   │   └── models.py
│   ├── static/
│   │   ├── css/
│   │   ├── img/
│   │   └── js/
│   ├── templates/
│   │   ├── base.html
│   │   ├── cards.html
│   │   ├── dashboard.html
│   │   ├── deposit.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── subscription.html
│   │   ├── transactions.html
│   │   ├── transfer.html
│   │   ├── users.html
│   │   ├── welcome.html
│   │   └── withdrawal.html
│   └── utils/
│       └── pdf_generator.py
├── config.py
├── flask_session/   # runtime session storage
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── b13909770384_add_pin_column_to_card.py
│       └── ccadf495c3e3_create_login_table.py
├── populate_random_db.py
├── requirements.txt
├── run.py
└── securebank.db

````

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/secure-banking-ai.git
cd secure-banking-ai
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python run.py
```

App will be available at `http://localhost:5000/`

---

##  AI Model (Fraud Detection)

* **Input Features**: transaction amount, type, location, user frequency, etc.
* **Algorithm**: Random Forest / XGBoost
* **Output**: Legitimate or Fraudulent transaction
* **Explainability**: Optional SHAP integration

---

##  Future Enhancements

* 2FA using Twilio for login/transaction
* Blockchain-style transaction logging
* SHAP/LIME explanations for model predictions
* Real-time notifications to admin

---

##  License

This project is licensed under the **MIT License**.

---

##  Contributing

Pull requests are welcome! Please open an issue first to discuss proposed changes.

