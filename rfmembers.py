from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, g, abort

from flask.ext.script import Manager

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.assets import Environment, Bundle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['ASSETS_DEBUG'] = True # TODO: set this to false in production
app.secret_key = "very secret"

assets = Environment(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    term = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    settled_by = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)

    created_session = db.relationship("Session", foreign_keys=[created_by], backref="created_memberships")
    settled_session = db.relationship("Session", foreign_keys=[settled_by], backref="settled_memberships")

    def is_free(self):
        return self.price == 0

def parse_price(text):
    if text == 'free':
        return 0
    else:
        return 50

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)

    def can(self, action):
        if self.level == 'Admin':
            return True

        if action == 'settlement':
            return self.level == 'SM'

        if action == 'memberships_list':
            return self.level == 'SM'

        if action == 'memberships_new':
            return True

        return False

# TODO: Move these out to a config-file
PASSWORDS = {
    'Funk': 'funk',
    'SM': 'sm',
    'Admin': 'admin',
}

@app.before_request
def before_request():
    if 'session_id' in session:
        sess = Session.query.get(session['session_id'])
        setattr(g, 'sess', sess)
    else:
        setattr(g, 'sess', None)


def logout():
    session.pop('session_id')

def requires(action):
    def decorator(func):
        @wraps(func)
        def route():
            if g.sess and g.sess.can(action):
                return func()
            else:
                abort(404)
        return route
    return decorator

@app.route('/')
def index():
    if g.sess is None:
        return render_template('index.html')
    else:
        return redirect(url_for('memberships_new'))

@app.route('/sessions/new')
def sessions_new():
    level = request.args['level']
    description = request.args['description']
    return render_template('sessions/new.html', level=level, description=description)

@app.route('/sessions/new', methods=['POST'])
def sessions_create():
    level = request.form["level"]
    real_password = PASSWORDS[request.form["level"]]

    if real_password != request.form["password"]:
        # TODO: Show error
        return sessions_new()

    sess = Session(
        level=level,
        description=request.form.get("description", "Unknown"),
    )
    db.session.add(sess)
    db.session.commit()
    session["session_id"] = sess.id
    return redirect(url_for('index'))

@app.route('/sessions/delete', methods=['POST'])
def sessions_destroy():
    g.sess.closed_at = datetime.utcnow()
    logout()
    return redirect(url_for('index'))

@app.route('/memberships/new')
@requires('memberships_new')
def memberships_new():
    last_memberships = Membership.query.order_by(db.desc('created_at')).limit(10)
    membership = Membership(name=request.args.get('name', ''))
    return render_template('memberships/new.html', membership=membership, last_memberships=last_memberships)

@app.route('/memberships/new', methods=['POST'])
@requires('memberships_new')
def memberships_create():
    membership = Membership(
        name=request.form["name"],
        price=parse_price(request.form["price"]),
        term="V15", # TODO: Don't hard-code right here
        created_by=g.sess.id
    )
    if membership.name.strip() == '':
        return render_template('memberships/new.html', membership=membership)

    db.session.add(membership)
    db.session.commit()
    return redirect(url_for('memberships_new'))

@app.route('/memberships/diff')
def memberships_diff():
    # Default is a week backwards
    from_date = datetime.utcnow() - timedelta(days=7)

    memberships_added = Membership.query.filter(Membership.created_at >
            from_date).all()
    cost = sum([membership.price for membership in memberships_added])

    return render_template('memberships/diff.html',
            memberships_added=memberships_added, from_date=from_date, cost=cost)

@app.route('/memberships/diff', methods=['POST'])
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
@requires('memberships_list')
def memberships_list():
    memberships = Membership.query.all()
    return render_template('memberships/list.html', memberships=memberships)

@app.route('/api/names', methods=['GET'])
def api_names():
    member_names = [m.name for m in Membership.query.all()]
    data = { "member_names" : member_names }
    return jsonify(**data)

if __name__ == '__main__':
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()
