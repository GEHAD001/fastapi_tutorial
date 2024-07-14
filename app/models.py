from sqlalchemy import TIMESTAMP, Column, Integer, LargeBinary, String, Boolean, ForeignKey, text
from sqlalchemy.orm import relationship
from .database import Base

class Post(Base):

    __tablename__ = 'posts'

    id = Column(Integer,primary_key=True,nullable=False)
    title = Column(String,nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean,server_default='FALSE',nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    user = relationship('User') # Fetch Data from User Model


class User(Base):

    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


# class File(Base):
#     __tablename__ = "files"
#     id = Column(Integer, primary_key=True, index=True)
#     filename = Column(String, index=True)
#     dir = Column(String)

class Likes(Base):
    __tablename__ = "likes"
    user_id = Column(Integer, ForeignKey('users.id',ondelete="CASCADE"),  primary_key=True, nullable=False, )
    post_id = Column(Integer, ForeignKey('posts.id',ondelete="CASCADE"),  primary_key=True, nullable=False, )

    user = relationship('User')
    post = relationship('Post')