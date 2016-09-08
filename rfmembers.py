import string
from datetime import datetime, timedelta
import time
from pytz import timezone
import pytz
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, g, abort
from calendar import month_name
from collections import defaultdict

from flask_sqlalchemy import SQLAlchemy
from flask_assets import Environment, Bundle
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['ASSETS_DEBUG'] = True
app.config['SECRET_KEY'] = "development key"
app.config['TIMEZONE'] = 'Europe/Oslo'
app.config['TERM'] = "V16"
app.config['PRICE'] = 50
app.config['PASSWORDS'] = {
    'Funk': 'funk',
    'SM': 'sm',
    'Admin': 'admin',
    'Superadmin': 'superadmin',
}
app.config['BLACKLIST'] = []

app.config.from_pyfile('production.cfg', silent=True)

tz = timezone(app.config['TIMEZONE'])

assets = Environment(app)

db = SQLAlchemy(app)

def compute_queryname(context):
    return context.current_parameters['name'].lower()

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column('name', db.Text, nullable=False)
    queryname = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    term = db.Column(db.Text, nullable=False)
    account = db.Column(db.Text, nullable=False) # Entrance/Wristband/Lifetime/Unknown
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    settled_by = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)

    created_session = db.relationship("Session", foreign_keys=[created_by], backref="created_memberships")
    settled_session = db.relationship("Session", foreign_keys=[settled_by], backref="settled_memberships")

    valid_term = (term == "Lifetime") | (term == app.config['TERM'])

    @hybrid_property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.queryname = value.lower()

    def is_free(self):
        return self.price == 0

    ALPHABET = "".join(str(x) for x in xrange(10))
    ALPHABET += string.ascii_uppercase

    ALPHABET = ALPHABET\
        .replace("O", "")\
        .replace("I", "") # too similar to 1

    def code(self):
        # convert to Unix epoch
        epoch = int(time.mktime(self.created_at.timetuple()))
        code = ""
        while epoch > 0:
            epoch, i = divmod(epoch, len(self.ALPHABET))
            code = self.ALPHABET[i] + code
        return code

def price_for_term(term):
    if term == 'Lifetime':
        return app.config['PRICE'] * 10
    else:
        return app.config['PRICE']

levels = ['Funk', 'SM', 'Admin', 'Superadmin']

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)

    def is_atleast(self, level):
        return levels.index(self.level) >= levels.index(level)

    def can(self, action, thing=None):
        if self.level == 'Superadmin':
            return True

        if action == 'settlement':
            return self.is_atleast('SM')

        if action == 'settlement_all':
            return self.is_atleast('Admin')

        if action == 'memberships_new':
            return True

        if action == 'reports':
            return self.is_atleast('Admin')

        if action == 'delete':
            # We can only delete our own memberships which are not settled
            if isinstance(thing, Membership):
                if thing.settled_by is None:
                    return thing.created_by == self.id

        if action == 'edit':
            if isinstance(thing, Membership):
                return True

        return False

@app.before_request
def before_request():
    if 'session_id' in session:
        sess = Session.query.get(session['session_id'])
        # Closed sessions are not valid
        if sess.closed_at is not None:
            sess = None
        # Old sessions are not valid
        if (datetime.now() - sess.created_at) > timedelta(days = 1):
            sess = None
        setattr(g, 'sess', sess)
    else:
        setattr(g, 'sess', None)

@app.context_processor
def inject_helpers():
    def localize(d):
        if d.tzinfo is None:
            d = d.replace(tzinfo=pytz.utc)
        return d.astimezone(tz)
    def latest_born_date():
        now = datetime.now()
        now = now.replace(year=now.year-18) - timedelta(days = 1)
        return now
    return dict(
        localize=localize,
        latest_born_date=latest_born_date
    )

def logout():
    session.pop('session_id')

def requires(action):
    def decorator(func):
        @wraps(func)
        def route(*args, **kwargs):
            if g.sess and g.sess.can(action):
                return func(*args, **kwargs)
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
def sessions_new(did_fail=False):
    level = request.args['level']
    description = request.args['description']
    return render_template('sessions/new.html', level=level, description=description, did_fail=did_fail)

@app.route('/sessions/new', methods=['POST'])
def sessions_create():
    level = request.form["level"]
    real_password = app.config['PASSWORDS'][request.form["level"]]

    if real_password != request.form["password"]:
        return sessions_new(did_fail=True)

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
    db.session.commit()
    logout()
    return redirect(url_for('index'))

@app.route('/memberships/new')
@requires('memberships_new')
def memberships_new():
    last_memberships = Membership.query.filter(Membership.valid_term).order_by(db.desc('created_at')).limit(10)
    term = request.args.get('term', app.config['TERM'])
    membership = Membership(term=term, account="Entrance")
    membership.price = price_for_term(membership.term)
    return render_template('memberships/new.html', membership=membership, last_memberships=last_memberships)

@app.route('/memberships/new', methods=['POST'])
@requires('memberships_new')
def memberships_create():
    membership = Membership(
        name=request.form["name"],
        term=request.form["term"],
        account=request.form["account"],
        created_by=g.sess.id
    )
    membership.price = price_for_term(membership.term)

    if membership.term == "Lifetime":
        membership.account = "Lifetime"

    errors = []
    if membership.name.strip() == '':
        errors.append("Name is required")

    if len(errors) > 0:
        return render_template('memberships/new.html', membership=membership, errors=errors)

    db.session.add(membership)
    db.session.commit()
    return redirect(url_for('memberships_new', term=membership.term))

@app.route('/memberships/<id>/edit')
def memberships_edit(id):
    mem = Membership.query.get(id)
    return render_template('memberships/edit.html', membership=mem)

@app.route('/memberships/<id>/delete', methods=['POST'])
@requires('memberships_new')
def memberships_destroy(id):
    mem = Membership.query.get(id)
    if g.sess.can('delete', mem):
        db.session.delete(mem)
        db.session.commit()
    return redirect(url_for('memberships_new'))

@app.route('/memberships/search')
def memberships_search():
    query_string = request.args['q']
    query = Membership.query.filter(Membership.valid_term)
    for part in query_string.split():
        like_string = '%' + part.lower() + '%'
        query = query.filter(Membership.queryname.like(like_string))

    limit = 10
    memberships = list(query.order_by(db.desc('created_at')).limit(limit))

    banned = []

    if len(memberships) < limit:
        # Search in blacklist
        banned = app.config["BLACKLIST"]
        for part in query_string.split():
            matches = lambda name: part.lower() in name.lower()
            banned = filter(matches, banned)

    return render_template('memberships/table.html', memberships=memberships, banned=banned)

@app.route('/memberships/settle')
@requires('settlement')
def memberships_settle():
    max_id = db.session.query(db.func.max(Membership.id)).scalar()

    if g.sess.can('settlement_all'):
        account = request.args.get('account', 'Entrance')
    else:
        account = "Entrance"

    sessions = db.session.query(
        db.func.count(Membership.created_by),
        db.func.sum(Membership.price),
        Session
    ) \
        .group_by(Membership.created_by) \
        .filter(Membership.account == account) \
        .filter(Membership.settled_by == None) \
        .filter(Membership.id <= max_id) \
        .join(Membership.created_session) \
        .all()

    summary = {
        'count': sum(count for count,_,_ in sessions),
        'price': sum(price for _,price,_ in sessions),
    }

    return render_template('memberships/settle.html', sessions=sessions, summary=summary, max_id=max_id, account=account)

@app.route('/memberships/settle', methods=['POST'])
@requires('settlement')
def memberships_settle_submit():
    max_id = request.form["max_id"]
    if g.sess.can('settlement_all'):
        account = request.form['account']
    else:
        account = "Entrance"

    update = db.update(Membership) \
        .where(Membership.account == account) \
        .where(Membership.settled_by == None) \
        .where(Membership.id <= max_id) \
        .values(settled_by=g.sess.id) \
        .values(queryname=Membership.queryname)

    db.session.execute(update)
    db.session.commit()
    return redirect(url_for('memberships_settle', account=account))

@app.route('/memberships')
@requires('memberships_list')
def memberships_list():
    memberships = Membership.query.all()
    return render_template('memberships/list.html', memberships=memberships)

@app.route('/reports')
@requires('reports')
def reports():
    membership_count = db.session.query(
        db.func.count(Membership.id),
        Membership.term,
        db.func.strftime('%Y', Membership.created_at).label('year'),
        db.func.strftime('%W', Membership.created_at).label('week')
    ) \
        .group_by('year', 'week', Membership.term) \
        .order_by('year', 'week')

    terms = defaultdict(lambda: [])
    lifetime = 0

    for count, term, year, week in membership_count:
        if term == "Lifetime":
            lifetime += count
        else:
            terms[term].append({"count": count, "year": int(year), "week": week})

    summary = []
    for term in terms:
        summary.append({
            "name": term,
            "rows": terms[term],
            "total": sum(r["count"] for r in terms[term]),
            "year": int(term[1:]) + 2000,
            "sortkey": term[1:] + str(int(term[0] == 'H'))
        })

    summary.sort(key=lambda k: k["sortkey"], reverse=True)

    return render_template('reports.html', summary=summary, lifetime=lifetime)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

