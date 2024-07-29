from sqlalchemy import Column, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Emoji(Base):
    __tablename__ = 'emojis'

    id = Column(Text, primary_key=True)
    misskey_id = Column(Text, unique=True)
    name = Column(Text, unique=True)
    category = Column(Text)
    tags = Column(Text)
    user_id = Column(Text, ForeignKey('users.id'))
    url = Column(Text)
    risk_id = Column(Text, ForeignKey('risks.id'))
    created_at = Column(Text)
    updated_at = Column(Text)

    users = relationship('User')
    risks = relationship('Risk')

class User(Base):
    __tablename__ = 'users'

    id = Column(Text, primary_key=True)
    misskey_id = Column(Text, unique=True)
    username = Column(Text, unique=True)

class Risk(Base):
    __tablename__ = 'risks'

    id = Column(Text, primary_key=True)
    is_checked = Column(Integer, CheckConstraint('is_checked == 0 OR is_checked == 1'))
    level = Column(Integer, CheckConstraint('level >= 0 AND level <= 3'))
    reason_genre = Column(Text, ForeignKey('reasons.id'))
    remark = Column(Text)
    created_at = Column(Text)
    updated_at = Column(Text)

    reasons = relationship('Reason')

class Reason(Base):
    __tablename__ = 'reasons'

    id = Column(Text, primary_key=True)
    reason = Column(Text, nullable=False)
    created_at = Column(Text)
    updated_at = Column(Text)


