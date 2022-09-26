import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from bd_models import create_tables, User_stranger, User, Stranger

DSN = 'postgresql://postgres:Motocikl@localhost:5432/netology_db'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

# user1 = User(name="Влад", age=26, gender="мужской", city="Москва")
# user2 = User(name="Маша", age=22, gender="женский", city="Санкт-Петербург")
# stranger1 = Stranger(name="Денис", age=25, gender="мужской", city="Санкт-Петербург")
# stranger2 = Stranger(name="Наташа", age=21, gender="женский", city="Москва")
#
# session.add_all([user1, user2, stranger1, stranger2])
# session.commit()
#
# for c in session.query(User).all():
#     print(c)
#
# for c in session.query(Stranger).all():
#     print(c)
if __name__ == '__main__':

    with open('fixtures/tests_data 2.json', 'r', encoding='utf-8') as fd:
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

age = input("Введите желаемый возраст партнера: ")
# gender = input("Введите желаемый пол партнера: ")
# city = input("Введите город партнера: ")

# for i in session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).\
#         join(User, User.id == User_stranger.user_id).\
#         filter(User.city.like(f"{city}")).all():
#     print(f"Партнер {i} подходит по Вашим параметрам")
#
# for i in session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).\
#         join(User, User.id == User_stranger.user_id).\
#         filter(User.gender.like(f"{gender}")).all():
#     print(f"Партнер {i} подходит по Вашим параметрам")

for i in session.query(Stranger).join(User_stranger, Stranger.id == User_stranger.stranger_id).\
        join(User, User.id == User_stranger.user_id).\
        filter(User.age.like(f"{age}")).all():
    print(f"Партнер {i} подходит по Вашим параметрам")

session.close()