from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from . import crud, models, schemas
from .database import DbSess, engine, get_db

# таблицы в бд (если нет)
models.OrmBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="API для библиотеки",
    description="API для управления авторами и книгами.",
    version="1.0.0"
)

@app.post("/authors", response_model=schemas.AuthorOutS, status_code=status.HTTP_201_CREATED, summary="Создать нового автора")
def cr_author_ep(auth_in: schemas.AuthorCrS, db: Session = Depends(get_db)):
    return crud.add_auth(db=db, auth_d=auth_in)

@app.get("/authors", response_model=List[schemas.AuthorOutS], summary="Получить список всех авторов")
def list_authors_ep(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    all_auths = crud.get_auths(db, skip=skip, limit=limit)
    return all_auths

@app.get("/authors/{author_id}", response_model=schemas.AuthorOutS, summary="Получить автора по ID")
def get_author_ep(author_id: int, db: Session = Depends(get_db)):
    auth = crud.get_auth(db, author_id=author_id)
    if auth is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    return auth

@app.put("/authors/{author_id}", response_model=schemas.AuthorOutS, summary="Обновить информацию об авторе")
def upd_author_ep(author_id: int, auth_in: schemas.AuthorCrS, db: Session = Depends(get_db)):
    auth = crud.get_auth(db, author_id=author_id)
    if auth is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    return crud.edit_auth(db=db, author_id=author_id, auth_d=auth_in)

@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить автора")
def del_author_ep(author_id: int, db: Session = Depends(get_db)):
    auth = crud.get_auth(db, author_id=author_id)
    if auth is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автор не найден")
    crud.del_auth(db=db, author_id=author_id)
    return

@app.post("/books", response_model=schemas.BookOutS, status_code=status.HTTP_201_CREATED, summary="Создать новую книгу")
def cr_book_ep(book_in: schemas.BookCrS, db: Session = Depends(get_db)):
    new_bk = crud.add_bk(db=db, bk_d=book_in)
    if new_bk is None: # нет автора - ошибка 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {book_in.author_id} не найден"
        )
    return new_bk

@app.get("/books", response_model=List[schemas.BookOutS], summary="Получить список книг")
def list_books_ep(author_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if author_id is not None:
        auth = crud.get_auth(db, author_id=author_id)
        if auth is None:
            pass
    all_bks = crud.get_bks(db, author_id=author_id, skip=skip, limit=limit)
    return all_bks

# пинг (для проверки)
@app.get("/ping")
def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
