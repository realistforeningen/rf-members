from flask import Flask, render_template

from flask.ext.script import Manager

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()

