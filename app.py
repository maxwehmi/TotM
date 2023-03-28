from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
with app.app_context():
    db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/') 
def index():
    return render_template('index.html')


@app.route('/imprint')
def imprint():
    return render_template('imprint.html')


@app.route('/redirect')
def redirect():
    return render_template('redirect.html')


@app.route('/unsub', methods=['POST','GET'])
def unsub():
    if request.method == 'POST':
        return render_template('unsub.html', call="USER_NOT_FOUND")
    else:
        return render_template('unsub.html')


if __name__ == "__main__":
    app.run(debug=True)