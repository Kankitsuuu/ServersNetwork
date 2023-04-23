from flask_login import UserMixin


class UserLogin(UserMixin):

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user.id)

    def get_from_db(self, user_id, model):
        self.__user = model.query.get(user_id)
        return self

    @property
    def username(self):
        return self.__user.username

    @property
    def is_admin(self):
        return self.__user.is_admin