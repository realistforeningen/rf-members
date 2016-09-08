from rfmembers import db

def setup():
    db.session.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY)')
    db.session.commit()

def migrate(func):
    args = {'version':func.__name__}
    is_done = db.session.execute('SELECT COUNT(*) FROM schema_migrations WHERE version = :version', args).scalar()
    if is_done:
        return

    print("[*] Running migration: %s" % args['version'])
    func()
    db.session.execute('INSERT INTO schema_migrations VALUES (:version)', args)
    db.session.commit()

def run():
    setup()

    @migrate
    def initial_schema():
        if db.engine.dialect.has_table(db.session, 'alembic_version'):
            if db.session.execute('SELECT count(*) FROM alembic_version').scalar():
                # Already migrated with the previous system
                db.session.execute('DROP TABLE alembic_version')
                return True

        db.session.execute("""
            CREATE TABLE session (
                id INTEGER NOT NULL,
                description TEXT NOT NULL,
                level TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                closed_at DATETIME,
                PRIMARY KEY (id)
            )
        """)

        db.session.execute("""
            CREATE TABLE membership (
                id INTEGER NOT NULL,
                name TEXT NOT NULL,
                queryname TEXT NOT NULL,
                price INTEGER NOT NULL,
                term TEXT NOT NULL,
                account TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                created_by INTEGER NOT NULL,
                settled_by INTEGER,
                PRIMARY KEY (id),
                FOREIGN KEY(created_by) REFERENCES session (id),
                FOREIGN KEY(settled_by) REFERENCES session (id)
            )
        """)

if __name__ == '__main__':
    run()
