from rfmembers import db, Membership, Session
from datetime import datetime
import sqlite3

import sys

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row

sess = Session(
    level="Admin",
    description="Import",
)
db.session.add(sess)
db.session.flush()

rows = conn.execute('select * from members')
for row in rows:
    if row['lifetime']:
        term = 'Lifetime'
    else:
        term = 'V15'

    timestamp = datetime.fromtimestamp(row['timestamp'])

    mem = Membership(
        name=row['first_name'] + u' ' + row['last_name'],
        term=term,
        price=row['paid'],
        account="Unknown",
        created_by=sess.id,
        settled_by=sess.id,
        created_at=timestamp,
    )
    db.session.add(mem)

db.session.commit()

