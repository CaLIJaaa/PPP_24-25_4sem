from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import OrmBase

# модель автора
class Author(OrmBase):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    books = relationship("Book", back_populates="author") # связь с книгами

# модель книги
class Book(OrmBase):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    year = Column(Integer)
    author_id = Column(Integer, ForeignKey("authors.id")) # внешний ключ

    author = relationship("Author", back_populates="books") # связь с автором 