from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify

from flask.ext.script import Manager
from flask.ext.httpauth import HTTPDigestAuth

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.assets import Environment, Bundle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['ASSETS_DEBUG'] = True # TODO: set this to false in production
app.config['SECRET_KEY'] = 'some_secret_key' # TODO Change before prod.

auth = HTTPDigestAuth()

users = {
    "admin" : "password", # For us devs
    "funk" : "password", # "Funker", can only register
    "mester" : "password" # Can do most everything
}

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

assets = Environment(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    term = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def is_free(self):
        return self.price == 0

def parse_price(text):
    if text == 'free':
        return 0
    else:
        return 50

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/memberships/new')
@auth.login_required
def memberships_new():
    membership = Membership(name=request.args.get('name', ''))
    return render_template('memberships/new.html', membership=membership)

@app.route('/memberships/new', methods=['POST'])
@auth.login_required
def memberships_create():
    membership = Membership(name=request.form["name"], price=parse_price(request.form["price"]), term="V15")
    if membership.name.strip() == '':
        return render_template('memberships/new.html', membership=membership)

    db.session.add(membership)
    db.session.commit()
    return redirect(url_for('memberships_list'))

@app.route('/memberships/diff')
@auth.login_required
def memberships_diff():
    # Default is a week backwards
    from_date = datetime.utcnow() - timedelta(days=7)

    memberships_added = Membership.query.filter(Membership.created_at >
            from_date).all()
    cost = sum([membership.price for membership in memberships_added])

    return render_template('memberships/diff.html',
            memberships_added=memberships_added, from_date=from_date, cost=cost)

@app.route('/memberships/diff', methods=['POST'])
@auth.login_required
def memberships_diff_formdate():
    # New date from form
    try:
        from_date = datetime.strptime(request.form["fromDate"],
                '%H:%M:%S %d-%m-%Y')
    except Exception, e:
        return memberships_diff()

    memberships_added = Membership.query.filter(Membership.created_at >
            from_date).all()
    cost = sum([membership.price for membership in memberships_added])

    return render_template('memberships/diff.html',
            memberships_added=memberships_added, from_date=from_date, cost=cost)

@app.route('/memberships')
@auth.login_required
def memberships_list():
    memberships = Membership.query.all()
    return render_template('memberships/list.html', memberships=memberships)

@app.route('/api/names', methods=['GET'])
@auth.login_required
def api_names():
    member_names = [m.name for m in Membership.query.all()]
    data = { "member_names" : member_names }
    return jsonify(**data)

if __name__ == '__main__':
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()

