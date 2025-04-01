from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for sessions

# Dummy user data (Replace this with actual database checks)
users = {
    "user@example.com": {"password": "password123"}
}


# Route for the home page (index.html)
@app.route('/')
def index():
    return render_template('signin.html')


# Route for the sign-up page (signup.html)
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/patients')
def patients():
    return render_template('patients.html')


# Route for the sign-in page (sign.html)
@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        # Get email and password from form
        email = request.form['email']
        password = request.form['password']

        # Check if user exists and password is correct
        if email in users and users[email]["password"] == password:
            # Store user info in session
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            # Invalid credentials, show an error message
            return render_template('signin.html', error="Invalid credentials")

    return render_template('signin.html')


# Route for the dashboard page
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        # If the user is not logged in, redirect to the sign-in page
        return redirect(url_for('sign'))

    # Display the dashboard content (user info or personalized content)
    return render_template('index.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('sign'))


if __name__ == "__main__":
    app.run(debug=True)
