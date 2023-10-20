from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def registerpage():
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def loginpage():
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug = True)