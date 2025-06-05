from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas

# ----- Авторы CRUD -----
def get_auth(db: Session, author_id: int): # взять автора
    return db.query(models.Author).filter(models.Author.id == author_id).first()

def get_auths(db: Session, skip: int = 0, limit: int = 100): # всех авторов
    return db.query(models.Author).offset(skip).limit(limit).all()

def add_auth(db: Session, auth_d: schemas.AuthorCrS): # созд автора
    new_a = models.Author(name=auth_d.name)
    db.add(new_a)
    db.commit()
    db.refresh(new_a)
    return new_a

def edit_auth(db: Session, author_id: int, auth_d: schemas.AuthorCrS): # апдейт автора
    auth = db.query(models.Author).filter(models.Author.id == author_id).first()
    if auth:
        auth.name = auth_d.name
        db.commit()
        db.refresh(auth)
    return auth

def del_auth(db: Session, author_id: int): # удалить автора
    auth = db.query(models.Author).filter(models.Author.id == author_id).first()
    if auth:
        # каскадное не требовалось для автора
        db.delete(auth)
        db.commit()
    return auth

# ----- Книги CRUD -----
def get_bk(db: Session, book_id: int): # взять книгу
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_bks(db: Session, author_id: Optional[int] = None, skip: int = 0, limit: int = 100): # все книги (можно по автору)
    q = db.query(models.Book)
    if author_id is not None:
        q = q.filter(models.Book.author_id == author_id)
    return q.offset(skip).limit(limit).all()

def add_bk(db: Session, bk_d: schemas.BookCrS): # созд книгу
    auth_exists = get_auth(db, bk_d.author_id)
    if not auth_exists:
        return None # нет автора - нет книги
    new_b = models.Book(title=bk_d.title, year=bk_d.year, author_id=bk_d.author_id)
    db.add(new_b)
    db.commit()
    db.refresh(new_b)
    return new_b
