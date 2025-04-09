from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import pandas as pd
from io import StringIO
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for sessions

# Dummy user data (Replace this with actual database checks)
users = {
    "user@example.com": {"password": "password123"}
}
s3 = boto3.client('s3', aws_access_key_id='AKIAXYKJUQCRERIV5OAR', aws_secret_access_key='dWoW0AoPOIRTcM9rlFHNDvASzcSP1/IRKIWiZ5HH', region_name='ap-south-1')


def fetch_patient_data():
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket='data-engineering-bucket', Key='Analyzed_Health_Condition_Data_Base.csv')
    csv_data = obj['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    print(df.head())  # Debugging line to check the data
    # Optional: Convert healthcare_target to readable string
    df['status'] = df['healthcare_target'].apply(lambda x: 'Good' if x == 1 else 'Bad')

    # Convert each row to dict
    return df.to_dict(orient='records')


# Route for the home page (index.html)
@app.route('/')
def index():
    return render_template('signin.html')


# Route for the sign-up page (signup.html)
@app.route('/signup')
def signup():
    return render_template('signup.html')


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


@app.route('/patients')
def load_patients_data():
    try:
        # Fetch the file from S3
        obj = s3.get_object(Bucket='data-engineering-bucket', Key='Analyzed_Health_Condition_Data_Base.csv')
        csv_data = obj['Body'].read().decode('utf-8')

        # Convert CSV data into a DataFrame
        df = pd.read_csv(StringIO(csv_data))

        # Replace the healthcare_target values with 'Good' and 'Bad'
        df['healthcare_target'] = df['healthcare_target'].replace({1: 'Good', 0: 'Bad'})

        # Optionally, limit the rows shown to avoid long output (adjust as necessary)
        patients_data = df.head(10).to_html(classes='table table-striped')

        # Render the 'patients.html' template, passing the patients data
        return render_template('patients.html', patients_data=patients_data)

    except Exception as e:
        return f"<h2>S3 Connection Failed:</h2><pre>{str(e)}</pre>"


@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('sign'))

@app.route('/test_s3')
def test_s3_connection():
    try:
        # Fetch the file
        obj = s3.get_object(Bucket='data-engineering-bucket', Key='Analyzed_Health_Condition_Data_Base.csv')
        csv_data = obj['Body'].read().decode('utf-8')

        # Convert to DataFrame
        df = pd.read_csv(StringIO(csv_data))

        # Optionally show only a few rows to avoid long output
        html_table = df.head(10).to_html(classes='table table-striped')

        return f"<h2>S3 Connection Successful! Showing Data:</h2>{html_table}"
    except Exception as e:
        return f"<h2>S3 Connection Failed:</h2><pre>{str(e)}</pre>"


if __name__ == "__main__":
    app.run(debug=True)
