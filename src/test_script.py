import requests
import os
import sqlite3
import json

# Debugging git repo
# Use environment variables for sensitive data
API_KEY = os.getenv("API_KEY", "")
PASSWORD = os.getenv("PASSWORD", "")

# VULNERABLE: Hardcoded secrets (will be detected by Gitleaks)
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
DATABASE_PASSWORD = "supersecretpassword123"
STRIPE_API_KEY = "sk_live_51AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"

def make_request(url):
    """Make a secure request"""
    response = requests.get(url, timeout=10)
    return response.json() if response.status_code == 200 else None

# VULNERABLE: SQL Injection (will be detected by Semgrep)
def get_user_by_id(user_id):
    """Vulnerable function with SQL injection"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: Direct string interpolation in SQL query
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

def search_users(search_term):
    """Another SQL injection vulnerability"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: String concatenation in SQL
    query = "SELECT * FROM users WHERE name LIKE '%" + search_term + "%'"
    cursor.execute(query)
    return cursor.fetchall()

def authenticate_user(username, password):
    """Vulnerable authentication with SQL injection"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: Direct SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    return user is not None

# VULNERABLE: Command Injection (will be detected by Semgrep)
def run_command(cmd):
    """Vulnerable command execution"""
    import subprocess
    # VULNERABLE: Shell injection
    os.system(f"ping -c 1 {cmd}")
    subprocess.call(f"echo {cmd}", shell=True)

# VULNERABLE: XSS (Cross-Site Scripting) - will be detected by Semgrep
def render_user_comment(comment):
    """Vulnerable HTML rendering"""
    # VULNERABLE: Direct HTML injection without sanitization
    html = f"<div>{comment}</div>"
    return html

def build_response(user_input):
    """Vulnerable response building"""
    # VULNERABLE: XSS vulnerability
    response = f"""
    <html>
        <body>
            <h1>Welcome {user_input}</h1>
        </body>
    </html>
    """
    return response

# VULNERABLE: Path Traversal (will be detected by Semgrep)
def read_file(filename):
    """Vulnerable file reading"""
    # VULNERABLE: Path traversal possible
    with open(f"/data/{filename}", "r") as f:
        return f.read()

# VULNERABLE: Insecure deserialization
def load_user_data(data):
    """Vulnerable JSON deserialization"""
    # VULNERABLE: Unsafe deserialization
    user_data = eval(data)  # DANGEROUS: eval() is unsafe
    return user_data

# VULNERABLE: Hardcoded credentials
DB_CONFIG = {
    "host": "localhost",
    "user": "admin",
    "password": "admin123",  # VULNERABLE: Hardcoded password
    "database": "mydb"
}

# VULNERABLE: API keys in code
STRIPE_SECRET = "sk_live_51AbCdEfGhIjKlMnOpQrStUvWxYz"
TWILIO_AUTH_TOKEN = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
JWT_SECRET = "my-super-secret-jwt-key-change-in-production"

# Run again
if __name__ == "__main__":
    # Test vulnerable functions
    user = get_user_by_id("1")
    results = search_users("test")
    authenticated = authenticate_user("admin", "password")

    #Re run with updated quality gates