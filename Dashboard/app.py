import pymysql
from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import pandas as pd
from io import StringIO
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for sessions

# PostgreSQL Database connection details
DB_HOST = 'localhost'
DB_USER = 'postgres'
DB_PASSWORD = '12345'
DB_NAME = 'medimy'
DB_PORT = 5433  # Default PostgreSQL port

def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            port=DB_PORT
        )
        return connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None
    

s3 = boto3.client('s3', aws_access_key_id='AKIAXYKJUQCRERIV5OAR', aws_secret_access_key='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', region_name='ap-south-1')


def fetch_patient_data():
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket='data-engineering-bucket', Key='device_output.csv')
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

        # Connect to the database
        connection = connect_to_db()
        if connection:
            try:
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                # Query the admin table to check credentials
                query = "SELECT * FROM admin WHERE email = %s AND password = %s;"
                cursor.execute(query, (email, password))
                admin = cursor.fetchone()
                cursor.close()
                connection.close()

                if admin:
                    # Store user info in session
                    session['user'] = admin['email']
                    return redirect(url_for('dashboard'))
                else:
                    # Invalid credentials, show an error message
                    return render_template('signin.html', error="Invalid credentials")
            except Exception as e:
                print(f"Error querying the database: {e}")
                return render_template('signin.html', error="An error occurred. Please try again.")
        else:
            return render_template('signin.html', error="Database connection failed.")

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
        # Step 1: Load CSV from S3
        obj = s3.get_object(Bucket='data-engineering-bucket', Key='device_output.csv')
        csv_data = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_data))

        # Ensure consistent column names
        if 'user_id' in df.columns:
            df.rename(columns={'user_id': 'userid'}, inplace=True)

        # Step 2: Connect to DB
        connection = connect_to_db()
        if not connection:
            return "Database connection failed."
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Step 3: Fetch assignments with device_id and userid
        cursor.execute('SELECT * FROM assignments;')
        assignments = pd.DataFrame(cursor.fetchall())

        # Step 4: Fetch user names
        cursor.execute('SELECT userid, name FROM "user";')
        users = pd.DataFrame(cursor.fetchall())

        cursor.close()
        connection.close()

        # Step 5: Merge assignments with usernames
        assignments = assignments.merge(users, on='userid', how='left')

        # Step 6: Merge with S3 CSV on device_id
        merged = assignments.merge(df, on='device_id', how='inner', suffixes=('_db', '_s3'))

        # Step 7: Replace health_condition values
        if 'health_condition' in merged.columns:
            merged['health_condition'] = merged['health_condition'].replace({1: 'Good', 0: 'Bad'})


        final_df = merged[['device_id', 'userid', 'name', 'temperature', 'oxygen_saturation',
                           'heart_rate', 'timestamp', 'respiratory_rate',
                           'health_condition', 'health_condition_warning',
                           'cvd_condition', 'cvd_condition_warning']].head(20)

        # Step 8: Render to template
        return render_template('patients.html', patients=final_df.to_dict(orient='records'))

    except Exception as e:
        return f"<h2>Error:</h2><pre>{str(e)}</pre>"



@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('sign'))

def get_oxygen_level_data():
    obj = s3.get_object(Bucket='data-engineering-bucket', Key='device_output.csv')
    csv_data = obj['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Group by time for trend
    trend_df = df.groupby(['timestamp']).oxygen_saturation.mean().reset_index()

    # Group by user/device for stats
    stats_df = df.groupby('userid').oxygen_saturation.mean().reset_index()

    return {
        "trend": trend_df.to_dict(orient='records'),
        "stats": stats_df.to_dict(orient='records')
    }


@app.route('/assign_device', methods=['GET', 'POST'])
def assign_device():
    connection = connect_to_db()
    if not connection:
        return "Database connection failed."

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        # Fetch users from the user table
        cursor.execute('SELECT "userid", "name" FROM "user";')  # Replace "fullname" with your actual column name
        users = cursor.fetchall()

        # Fetch devices from the device table
        cursor.execute('SELECT "device_id" FROM "device";')
        devices = cursor.fetchall()

        if request.method == 'POST':
            # Handle form submission
            user_id = request.form['user_id']
            device_id = request.form['device_id']

            # Insert the assignment into a hypothetical assignments table
            cursor.execute(
                "INSERT INTO assignments (userid, device_id) VALUES (%s, %s);",
                (user_id, device_id)
            )
            connection.commit()
            return render_template('assign_device.html', users=users, devices=devices, success="Device assigned successfully!")

        return render_template('assign_device.html', users=users, devices=devices)

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while fetching data."
    finally:
        cursor.close()
        connection.close()



if __name__ == "__main__":
    app.run(debug=True)
