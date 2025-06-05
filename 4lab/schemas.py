from pydantic import BaseModel, validator
from typing import List, Optional
import datetime

# --- Схемы Книг ---
class BookS(BaseModel):
    title: str
    year: int
    author_id: int

    @validator('year') # валидация года
    def check_year(cls, y):
        if y > datetime.date.today().year:
            raise ValueError('Год издания не может быть в будущем')
        return y

class BookCrS(BookS):
    pass

class BookOutS(BookS):
    id: int

    class Config:
        from_attributes = True

# --- Схемы Авторов ---
class AuthorS(BaseModel):
    name: str

class AuthorCrS(AuthorS):
    pass

class AuthorOutS(AuthorS):
    id: int
    # books: List[BookOutS] = [] # потом можно, если BookOutS тут будет

    class Config:
        from_attributes = True 