from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from .forms import LoginForm, SingupForm


auth_bp = Blueprint("auth_bp", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash("Logged in successfully!", category="success")
                # TODO: implement next function to redirect to the requested page after login in
                return redirect(url_for("inventory_bp.home"))
            else:
                flash("Incorrect user password combination.", category="error")
        else:
            flash("Incorrect user password combination.", category="error")
    form.flash_errors()
    return render_template("auth/login.html", user=current_user, form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth_bp.login"))


@auth_bp.route("/sign-up", methods=["GET", "POST"])
def sing_up():
    form = SingupForm()
    if form.validate_on_submit():
        email = form.email.data
        first_name = form.first_name.data
        password1 = form.password1.data
        password2 = form.password2.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.", category="error")
        elif password1 != password2:
            flash("Passwords are not the same", category="error")
        else:
            new_user = User(
                email=email,
                first_name=first_name,
                password=generate_password_hash(password1, method="sha256"),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created!", category="success")
            return redirect(url_for("inventory_bp.home"))
    form.flash_errors()
    return render_template("auth/sign_up.html", user=current_user, form=form)
