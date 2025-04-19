import pymysql
from flask import Flask, render_template, request, redirect, url_for, session,jsonify
import boto3
import pandas as pd
from io import StringIO
import psycopg2
from psycopg2.extras import RealDictCursor
import requests


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


# Define your Raspberry Pi API base URL (replace with actual IP or hostname of Pi)
RPI_API_BASE = "http://localhost:5050"  # Update this URL
AUTH_HEADER = {
    'Authorization': 'Bearer o92F2N30vZ1y9n84KDLsQ8kx3OeKZsmv'
}

@app.route('/device_configuration')
def device_configuration():
    # Fetch system information (CPU and memory) from the Pi API
    cpu_status = requests.get(f"{RPI_API_BASE}/status/cpu").json()
    memory_status = requests.get(f"{RPI_API_BASE}/status/memory").json()
    return render_template('device_configuration.html', cpu_status=cpu_status, memory_status=memory_status)


@app.route('/reboot-device', methods=['POST'])
def reboot_device():
    try:
        headers = {
            'Authorization': 'Bearer o92F2N30vZ1y9n84KDLsQ8kx3OeKZsmv'  # Replace with your actual token
        }
        response = requests.post("http://localhost:5050/reboot", headers=headers, timeout=5)

        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Reboot initiated.'})
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to initiate reboot. Status code: {response.status_code}',
                'response': response.text
            }), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/shutdown-device', methods=['POST'])
def shutdown_device():
    try:
        headers = {
            'Authorization': 'Bearer o92F2N30vZ1y9n84KDLsQ8kx3OeKZsmv'  # Replace with your actual token
        }

        response = requests.post("http://localhost:5050/shutdown", headers=headers, timeout=5)

        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Shutdown initiated.'})
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to initiate shutdown. Status code: {response.status_code}',
                'response': response.text
            }), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/restart-service', methods=['POST'])
def restart_service():
    try:
        payload = request.get_json()
        response = requests.post("http://localhost:5050/service/restart", headers=AUTH_HEADER, json=payload)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/stop-service', methods=['POST'])
def stop_service():
    try:
        payload = request.get_json()
        response = requests.post("http://localhost:5050/service/stop", headers=AUTH_HEADER, json=payload)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/start-service', methods=['POST'])
def start_service():
    try:
        payload = request.get_json()
        response = requests.post("http://localhost:5050/service/start", headers=AUTH_HEADER, json=payload)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/cpu-status', methods=['GET'])
def cpu_status():
    try:
        # Fetching CPU status from the external service
        response = requests.get("http://localhost:5050/status/cpu", headers=AUTH_HEADER)

        # Checking if the response is successful (status code 200)
        if response.status_code == 200:
            return jsonify(response.json()), response.status_code
        else:
            return jsonify({'status': 'error',
                            'message': f'Failed to fetch CPU status. Status code: {response.status_code}'}), response.status_code

    except Exception as e:
        # Returning an error message in case of an exception
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/memory-status', methods=['GET'])
def memory_status():
    try:
        # Fetching Memory status from the external service
        response = requests.get("http://localhost:5050/status/memory", headers=AUTH_HEADER)

        # Checking if the response is successful (status code 200)
        if response.status_code == 200:
            return jsonify(response.json()), response.status_code
        else:
            return jsonify({'status': 'error',
                            'message': f'Failed to fetch memory status. Status code: {response.status_code}'}), response.status_code

    except Exception as e:
        # Returning an error message in case of an exception
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/active-services', methods=['GET'])
def active_services():
    try:
        response = requests.get("http://localhost:5050/status/services", headers=AUTH_HEADER)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/train-svm', methods=['POST'])
def train_svm():
    try:
        payload = request.get_json()
        response = requests.post("http://localhost:5050/train-svm/", headers=AUTH_HEADER, json=payload)

        # Check if the response is valid JSON
        try:
            response_data = response.json()
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid JSON response from the server'}), 500

        return jsonify(response_data), response.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/experimental-data', methods=['GET'])
def experimental_data():
    return render_template('experimental.html')

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
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('sign'))

    try:
        userid = request.args.get('userid')

        # Load CSV from S3
        obj = s3.get_object(Bucket='data-engineering-bucket', Key='device_output.csv')
        csv_data = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_data))
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Connect to DB
        conn = connect_to_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all patients for dropdown
        cursor.execute('SELECT userid, name FROM "user";')
        patients = cursor.fetchall()

        oxygen_levels = []
        heart_rates = []
        timestamps = []
        selected_userid = None



        if userid:
            selected_userid = userid

            # Fetch the device ID assigned to this user
            cursor.execute("SELECT device_id FROM assignments WHERE userid = %s;", (userid,))
            assignment = cursor.fetchone()

            if assignment:
                device_id = assignment['device_id']
                user_df = df[df['device_id'] == device_id].sort_values('timestamp')
                oxygen_levels = user_df['oxygen_saturation'].tolist()
                heart_rates = user_df['heart_rate'].tolist()
                timestamps = user_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

        cursor.close()
        conn.close()

        return render_template('index.html',
                               user=session['user'],
                               patients=patients,
                               selected_userid=selected_userid,
                               oxygen_levels=oxygen_levels,
                               heart_rates=heart_rates,
                               timestamps=timestamps,
                               success=request.args.get('success'),
                               error=request.args.get('error'),
                               delete_success=request.args.get('delete_success'),
                               delete_error=request.args.get('delete_error'))


    except Exception as e:
        return f"<h2>Error in Dashboard:</h2><pre>{str(e)}</pre>"


@app.route('/delete_device', methods=['GET', 'POST'])
def delete_device():
    if 'user' not in session:
        return redirect(url_for('sign'))

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Fetch all assignments
        cursor.execute("SELECT * FROM assignments;")
        assignments = cursor.fetchall()
        print(assignments)  # Debugging line to check the data

        cursor.close()
        connection.close()

        # Render the template with assignments
        return render_template('delete_device.html', assignments=assignments)

    except Exception as e:
        print("Error:", e)
        return render_template('delete_device.html', delete_error="An error occurred while fetching assignments.")


@app.route('/unassign_device', methods=['POST'])
def unassign_device():
    if 'user' not in session:
        return redirect(url_for('sign'))

    # Get the assignment_id from the form submission
    assignment_id = request.form.get('assignment_id')

    try:
        # Connect to the database
        connection = connect_to_db()
        cursor = connection.cursor()

        # Check if the assignment exists using the assignment_id
        cursor.execute("SELECT * FROM assignments WHERE assignment_id = %s;", (assignment_id,))
        assignment = cursor.fetchone()

        if not assignment:
            # If no assignment is found, render with an error message
            return render_template('delete_device.html', delete_error="No assignment found with this ID.")

        # Unassign the device by setting device_id to NULL (without deleting the assignment)
        cursor.execute("""
            UPDATE assignments
            SET device_id = NULL
            WHERE assignment_id = %s;
        """, (assignment_id,))

        # Commit the changes to the database
        connection.commit()

        cursor.close()
        connection.close()

        # Redirect to the page with a success message
        return redirect(url_for('delete_device', delete_success="Device unassigned successfully."))

    except Exception as e:
        print("Unassign error:", e)
        # Render the page with an error message if an exception occurs
        return render_template('delete_device.html', delete_error="An error occurred during unassigning the device.")



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



@app.route('/patient_chart', methods=['GET', 'POST'])
def patient_chart():
    try:
        userid = request.args.get('userid')
        if not userid:
            return redirect(url_for('dashboard'))

        # Load CSV
        obj = s3.get_object(Bucket='data-engineering-bucket', Key='device_output.csv')
        csv_data = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_data))

        # DB Connection
        conn = connect_to_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch device_id for this user
        cursor.execute("SELECT * FROM assignments WHERE userid = %s;", (userid,))
        assignment = cursor.fetchone()

        if not assignment:
            return f"No device found for user ID {userid}"

        device_id = assignment['device_id']
        user_df = df[df['device_id'] == device_id]

        # Sort by timestamp for trend plotting
        user_df['timestamp'] = pd.to_datetime(user_df['timestamp'])
        user_df = user_df.sort_values('timestamp')
        timestamps = user_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        # Extract relevant data
        oxygen_levels = user_df['oxygen_saturation'].tolist()
        heart_rates = user_df['heart_rate'].tolist()

        # Define a mapping function
        def map_condition(value):
            return "Good" if value == 1 else "Bad" if value == 0 else "Unknown"

        # Fetch health_condition and cvd_condition
        health_condition = map_condition(user_df['health_condition'].iloc[-1]) if not user_df.empty else "Unknown"
        cvd_condition = map_condition(user_df['cvd_condition'].iloc[-1]) if not user_df.empty else "Unknown"
        # Get all users to populate dropdown
        cursor.execute('SELECT userid, name FROM "user";')
        patients = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('index.html',
                               patients=patients,
                               selected_userid=userid,
                               timestamps=timestamps,
                               oxygen_levels=oxygen_levels,
                               heart_rates=heart_rates,
                               health_condition=health_condition,
                               cvd_condition=cvd_condition)

    except Exception as e:
        return f"<h2>Error:</h2><pre>{str(e)}</pre>"


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
    app.run(host='0.0.0.0', port=5000, debug=True)
