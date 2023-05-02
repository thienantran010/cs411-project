from flask_login import UserMixin

from db import get_db


class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id = None, email = None, password = None):
        if user_id:
            db = get_db()
            user = db.execute(
                "SELECT * FROM user WHERE id = ?", (user_id,)
            ).fetchone()
            if not user:
                return None
            print(user[0])
            user = User(
                id_=user[0], name=user[1], email=user[2], profile_pic=user[3]
            )
            return user
        if email and password:
            db = get_db()
            user = db.execute(
                "SELECT * FROM user WHERE email = ?", (email,)
            ).fetchone()
            if not user:
                return None
            elif user[4] != password:
                print(f"Actual password is {user[4]}")
                return None
            user = User(
                id_=user[0], name=user[1], email=user[2], profile_pic=user[3]
            )
            return user

    @staticmethod
    def test(email):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE email = ?", (email,)
        ).fetchone()
        if not user:
            return None
        return user[0], user[1], user[2], user[3], user[4]
    
    @staticmethod
    def create(id_, name, email, profile_pic, password = None):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic, password)"
            " VALUES (?, ?, ?, ?, ?)",
            (id_, name, email, profile_pic, password),
        )
        db.commit()
