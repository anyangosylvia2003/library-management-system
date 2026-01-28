from flask import Flask, render_template, redirect, url_for, request
from extensions import db
from models import User, Book, Borrow
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        return "Invalid username or password"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/books', methods=['GET', 'POST'])
@login_required
def books():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        book = Book(title=title, author=author)
        db.session.add(book)
        db.session.commit()
    all_books = Book.query.all()
    return render_template('books.html', books=all_books)

@app.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    if not book.available:
        return "Book already borrowed"
    if request.method == 'POST':
        user_name = request.form['user_name']
        borrow = Borrow(user_name=user_name, book_id=book.id)
        book.available = False
        db.session.add(borrow)
        db.session.commit()
        return redirect(url_for('books'))
    return render_template('borrow.html', book=book)

@app.route('/borrowed')
@login_required
def borrowed_books():
    borrows = Borrow.query.filter_by(return_date=None).all()
    return render_template('borrowed.html', borrows=borrows)

@app.route('/return/<int:borrow_id>')
@login_required
def return_book(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    borrow.return_date = datetime.utcnow()
    borrow.book.available = True
    db.session.commit()
    return redirect(url_for('borrowed_books'))

# -------------------- RUN APP --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database created successfully")
    app.run(debug=True)