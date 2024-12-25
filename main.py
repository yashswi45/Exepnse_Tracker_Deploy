from datetime import date

import matplotlib
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.future import engine
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, Date
from werkzeug.security import generate_password_hash, check_password_hash
from form import RegisterForm, LoginForm, ExpenseForm  # Ensure the forms are defined in a file named `forms.py`

import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
from sqlalchemy.orm import Session
import logging
import logging
logging.basicConfig(level=logging.INFO)



matplotlib.use('Agg')

app = Flask(__name__)
# app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6s'

ckeditor = CKEditor(app)
Bootstrap(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated




# Database Configuration
class Base(DeclarativeBase):
    pass


# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myexpenses.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expen.db'



db = SQLAlchemy(model_class=Base)
db.init_app(app)



# User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


# Blog Post Table
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post")


# Comments Table
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


# Expense Table
# class Expense(db.Model):
#     __tablename__ = "expense"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     amount: Mapped[float] = mapped_column(Float, nullable=False)
#     description: Mapped[str] = mapped_column(String(100), nullable=False)
#     date: Mapped[date] = mapped_column(Date, nullable=False)
#     user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
#     user = relationship("User")


class Expense(db.Model):
    __tablename__ = "expense"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User")


# Create database tables
with app.app_context():
    db.create_all()



# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Registration route
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            flash("You've already signed up with this email, try logging in instead!", "warning")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Registration successful! Welcome to Expense Tracker.", "success")
            return redirect(url_for("add_expense"))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Please try again.", "danger")
            return redirect(url_for('register'))

    return render_template("register.html", form=form, current_user=current_user)


# Login route
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            flash("That email does not exist, please try again", "danger")
            return redirect(url_for("login"))

        elif not check_password_hash(user.password, password):
            flash("Incorrect password, please try again", "danger")
            return redirect(url_for("login"))

        else:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))

    return render_template("login.html", form=form, current_user=current_user)


# # Add expense route
# @app.route('/add_expense', methods=["GET", "POST"])
# @login_required
# def add_expense():
#     form = ExpenseForm()
#
#     if form.validate_on_submit():
#         new_expense = Expense(
#             amount=form.amount.data,
#             description=form.description.data,
#             date=form.date.data,
#             user_id=current_user.id
#         )
#         try:
#             db.session.add(new_expense)
#             db.session.commit()
#             flash("Expense added successfully!", "success")
#             return redirect(url_for('home'))
#         except Exception as e:
#             db.session.rollback()
#             flash("An error occurred while adding the expense.", "danger")
#             return redirect(url_for('add_expense'))
#
#     return render_template("add_expense.html", form=form)


# @app.route('/add_expense', methods=["GET", "POST"])
# @login_required
# def add_expense():
#     form = ExpenseForm()
#     expense_added = False
#
#     if form.validate_on_submit():
#         new_expense = Expense(
#             amount=form.amount.data,
#             description=form.description.data,
#             date=form.date.data,
#             user_id=current_user.id
#         )
#         try:
#             db.session.add(new_expense)
#             db.session.commit()
#             flash("Expense added successfully!", "success")
#             expense_added = True
#             return redirect(url_for('add_expense', expense_added=expense_added))
#         except Exception as e:
#             db.session.rollback()
#             flash("An error occurred while adding the expense.", "danger")
#             return redirect(url_for('add_expense'))
#
#     return render_template("add_expense.html", form=form, expense_added=expense_added)
#

# @app.route('/add_expense', methods=["GET", "POST"])
# @login_required
# def add_expense():
#     form = ExpenseForm()
#
#     if form.validate_on_submit():
#         new_expense = Expense(
#             amount=form.amount.data,
#             description=form.description.data,
#             date=form.date.data,
#             user_id=current_user.id
#         )
#         try:
#             db.session.add(new_expense)
#             db.session.commit()
#             flash("Expense added successfully!", "success")
#             return redirect(url_for('home'))  # Redirect to home or view_expenses
#         except Exception as e:
#             db.session.rollback()
#             flash("An error occurred while adding the expense.", "danger")
#             return redirect(url_for('add_expense'))
#
#     return render_template("add_expense.html", form=form)




@app.route('/add_expense', methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()
    logging.info("Expense form loaded")

    if form.validate_on_submit():  # This ensures that form data is valid
        logging.info(f"Form data: {form.amount.data}, {form.description.data}, {form.date.data}")
        new_expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            user_id=current_user.id  # The user ID is assigned to the current logged-in user
        )
        try:
            db.session.add(new_expense)  # Add expense to the session
            db.session.commit()  # Commit the transaction to the database
            flash("Expense added successfully!", "success")
            return redirect(url_for('home'))  # Redirect user back to home or another page
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            flash("An error occurred while adding the expense.", "danger")
            return redirect(url_for('add_expense'))

    return render_template("add_expense.html", form=form)


# @app.route('/add_expense', methods=["GET", "POST"])
# @login_required
# def add_expense():
#     form = ExpenseForm()
#     logging.info("Expense form loaded")
#
#     if form.validate_on_submit():
#         logging.info(f"Form data: {form.amount.data}, {form.description.data}, {form.date.data}")


# -----------------------------------------------------------------------------------------------------------------------

# GRAPH - ANALYTICS PAGE


@app.route('/analytics')
@login_required
def analytics():
    # Sample data extraction
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    data = [{'Amount': e.amount, 'Date': e.date} for e in expenses]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date
    df = df.sort_values('Date')

    # Monthly and Annual Summaries
    df_monthly = df.resample('ME', on='Date').sum()
    df_annual = df.resample('YE', on='Date').sum()

    # Line chart for Monthly Expenses
    plt.figure(figsize=(10, 5))
    plt.plot(df_monthly.index, df_monthly['Amount'], marker='o', linestyle='-')
    plt.title('Monthly Expenses')
    plt.xlabel('Month')
    plt.ylabel('Total Expense')
    plt.grid(True)

    # Convert plot to PNG image
    monthly_img = BytesIO()
    plt.savefig(monthly_img, format='png')
    monthly_img.seek(0)
    monthly_plot_url = base64.b64encode(monthly_img.getvalue()).decode('utf8')
    plt.close()

    # Line chart for Annual Expenses
    plt.figure(figsize=(10, 5))
    plt.plot(df_annual.index, df_annual['Amount'], marker='o', linestyle='-')
    plt.title('Annual Expenses')
    plt.xlabel('Year')
    plt.ylabel('Total Expense')
    plt.grid(True)

    # Convert plot to PNG image
    annual_img = BytesIO()
    plt.savefig(annual_img, format='png')
    annual_img.seek(0)
    annual_plot_url = base64.b64encode(annual_img.getvalue()).decode('utf8')
    plt.close()

    return render_template('analytics.html', monthly_plot_url=monthly_plot_url, annual_plot_url=annual_plot_url)


# -----------------------------------------------------------------------------------------------------------------------


# @app.route('/view_expenses')
# def view_expenses():
#     expenses = Expense.query.all()
#     return render_template('view_expenses.html', expenses=expenses)
#
#


@app.route('/delete_expense/<int:expense_id>', methods=["POST"])
@login_required
def delete_expense(expense_id):
    # Get the expense by ID
    expense_to_delete = Expense.query.get(expense_id)

    # Check if the current user is the owner of the expense
    if expense_to_delete and expense_to_delete.user_id == current_user.id:
        try:
            db.session.delete(expense_to_delete)
            db.session.commit()
            flash("Expense deleted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while deleting the expense.", "danger")
    else:
        flash("You do not have permission to delete this expense.", "danger")

    return redirect(url_for('view_expenses'))




@app.route('/view_expenses')
@login_required
def view_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()  # Fetch only the user's expenses
    return render_template('view_expenses.html', expenses=expenses)


# Logout route
@app.route('/logout')
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for('home'))


# Home route
@app.route('/')
def home():
    if current_user.is_authenticated:
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        return render_template('home.html', expenses=expenses)
    else:
        return render_template('home.html')


# About route
@app.route("/about")
def about():
    return render_template('about.html')


# Contacts route
@app.route("/contacts")
def contacts():
    return render_template('contacts.html')

with app.app_context():
    # Try to add a test entry
    test_expense = Expense(amount=100.0, description="Test expense", date=date.today(), user_id=1)
    db.session.add(test_expense)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)













