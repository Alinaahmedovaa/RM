from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Recipe
from flask_login import current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Смени със силен секретен ключ
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'YOUR_EMAIL@gmail.com'
app.config['MAIL_PASSWORD'] = 'YOUR_PASSWORD'
app.config['MAIL_DEFAULT_SENDER'] = 'YOUR_EMAIL@gmail.com'
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверка за съществуващ потребител с този имейл или потребителско име
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.')
            return redirect(url_for('register'))

        # Създаване на нов потребител
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user = User.query.filter_by(username=username, email=email).first()
        if user:
            # Изпращане на имейл с текущата парола
            msg = Message("Your Password for Recipe Manager", recipients=[email])
            msg.body = f"Hello {username},\n\nYour password is: {user.password}\n\nPlease log in and consider updating your password if you wish."
            mail.send(msg)
            flash('An email has been sent with your password.')
        else:
            flash('No account found with that username and email.')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/')
def index():
    category = request.args.get('category')
    ingredient = request.args.get('ingredient')
    max_time = request.args.get('max_time', type=int)

    recipes = Recipe.query

    if category:
        recipes = recipes.filter(Recipe.category == category)
    if ingredient:
        recipes = recipes.filter(Recipe.ingredients.contains(ingredient))
    if max_time:
        recipes = recipes.filter(Recipe.preparation_time <= max_time)

    recipes = recipes.all()
    return render_template('index.html', recipes=recipes)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category = request.form['category']
        preparation_time = int(request.form['preparation_time'])

        new_recipe = Recipe(
            name=name,
            ingredients=ingredients,
            instructions=instructions,
            category=category,
            preparation_time=preparation_time,
            user_id=current_user.id  # Свързване на рецептата с текущия потребител
        )
        db.session.add(new_recipe)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    recipe = Recipe.query.get_or_404(id)
    if request.method == 'POST':
        recipe.name = request.form['name']
        recipe.ingredients = request.form['ingredients']
        recipe.instructions = request.form['instructions']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', recipe=recipe)

@app.route('/delete/<int:id>')
def delete(id):
    recipe = Recipe.query.get_or_404(id)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Създава таблицата при първото стартиране
    app.run(debug=True)
