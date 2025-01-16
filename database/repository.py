from fastapi import Depends

from sqlalchemy.orm import Session

from database.connection import get_db


class UserRepository:
    def __init__(self, session: Session=Depends(get_db)):
        self.session = session


    def create_parent_user(self):
