from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

from flask.ext.script import Manager

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.assets import Environment, Bundle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['ASSETS_DEBUG'] = True # TODO: set this to false in production

assets = Environment(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    term = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/memberships/new')
def memberships_new():
    membership_name = request.args.get('name', '')
    return render_template('memberships/new.html', membership_name=membership_name)

@app.route('/memberships/new', methods=['POST'])
def memberships_create():
    membership = Membership(name=request.form["name"], price=request.form["price"], term="V15")
    db.session.add(membership)
    db.session.commit()
    return redirect(url_for('memberships_list'))

@app.route('/memberships')
def memberships_list():
    memberships = Membership.query.all()
    return render_template('memberships/list.html', memberships=memberships)

if __name__ == '__main__':
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()

