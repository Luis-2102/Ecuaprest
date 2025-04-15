from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from functools import wraps


app = Flask(__name__)
app.secret_key = 'ecuaprest_secret_key'  

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # This is a placeholder - in a real app, you would validate against a database
        if username == 'admin' and password == 'password':
            session['user_id'] = 1
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login.html'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('pages/samples/dashboard.html')

# Sample routes for different sections based on your directory structure
@app.route('/charts')
@login_required
def charts():
    return render_template('pages/charts/index.html')

@app.route('/forms')
@login_required
def forms():
    return render_template('pages/forms/index.html')

@app.route('/tables')
@login_required
def tables():
    return render_template('pages/tables/index.html')

@app.route('/documentation')
def documentation():
    return render_template('pages/documentation/index.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    app.run(debug=True)