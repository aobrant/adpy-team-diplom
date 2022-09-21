import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import create_tables, User_stranger, User, Stranger

DSN = 'postgresql://postgres: @localhost:5432/netology_db'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

with open('fixtures/tests_data.json', 'r') as fd:
    data = json.load(fd)

for record in data:
    model = {
        'user_stranger': User_stranger,
        'user': User,
        'stranger': Stranger,
    }[record.get('model')]
    session.add(model(id=record.get('pk'), **record.get('fields')))

session.commit()

for c in session.query(User).all():
    print(c)

session.close()