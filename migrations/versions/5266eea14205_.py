"""empty message

Revision ID: 5266eea14205
Revises: None
Create Date: 2015-07-30 13:14:10.848519

"""

# revision identifiers, used by Alembic.
revision = '5266eea14205'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('level', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('membership',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('queryname', sa.Text(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('term', sa.Text(), nullable=False),
    sa.Column('account', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('settled_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['session.id'], ),
    sa.ForeignKeyConstraint(['settled_by'], ['session.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('membership')
    op.drop_table('session')
    ### end Alembic commands ###
