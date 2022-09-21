import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class User_stranger(Base):
    __tablename__ = "user_stranger"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    stranger_id = sq.Column(sq.Integer, sq.ForeignKey("stranger.id"), nullable=False)

    users = relationship("User", back_populates="user_stranger1")
    strangers = relationship("Stranger", back_populates="user_stranger2")

class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    gender = sq.Column(sq.String(length=10), nullable=False)
    city = sq.Column(sq.String(length=30), nullable=False)

    user_stranger1 = relationship("User_stranger", back_populates="users")

    def __str__(self):
        return f'Номер ID - {self.id}, Имя - {self.name}, Возраст - {self.age}, Пол - {self.gender}, Город - {self.city}'

class Stranger(Base):
    __tablename__ = "stranger"

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    gender = sq.Column(sq.String(length=10), nullable=False)
    city = sq.Column(sq.String(length=30), nullable=False)

    user_stranger2 = relationship("User_stranger", back_populates="strangers")

    def __str__(self):
        return f'Номер ID - {self.id}, Имя - {self.name}, Возраст - {self.age}, Пол - {self.gender}, Город - {self.city}'

def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)