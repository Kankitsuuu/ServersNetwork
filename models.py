from flask_migrate import Migrate
from app import app
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<user id={self.id}>'

    def __str__(self):
        return self.username


class Servers(db.Model):
    __tablename__ = 'servers'
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(50))
    city = db.Column(db.String(50))
    ip = db.Column(db.String(50), unique=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def __repr__(self):
        return f'<server ip={self.ip}'


class Files(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    url = db.Column(db.String(255), unique=True)
    file_type = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    upload_vps = db.Column(db.Integer, db.ForeignKey('servers.id'))
    upload_time = db.Column(db.DateTime)

    fk_user = db.relationship('Users', backref='users', uselist=False)
    fk_vps = db.relationship('Servers', backref='servers', uselist=False)

    def __repr__(self):
        return f'<file id={self.id}'


class Replications(db.Model):
    __tablename__ = 'replications'
    id = db.Column(db.Integer, primary_key=True)
    from_vps = db.Column(db.Integer, db.ForeignKey('servers.id'))
    to_vps = db.Column(db.Integer, db.ForeignKey('servers.id'))
    action_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    action_type = db.Column(db.String(30))

    fk_from_vps = db.relationship('Servers', foreign_keys=[from_vps], lazy=True)
    fk_to_vps = db.relationship('Servers', foreign_keys=[to_vps], lazy=True)

    def __repr__(self):
        return f'<replication process id={self.id}'


class Actions(db.Model):
    __tablename__ = 'actions'
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.Integer, db.ForeignKey('servers.id'))
    username = db.Column(db.String(30))
    duration = db.Column(db.Float)
    action_time = db.Column(db.DateTime)
    action_type = db.Column(db.String(30))

    fk_server = db.relationship('Servers', lazy=True)