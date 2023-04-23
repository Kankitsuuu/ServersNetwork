import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOCAL_FOLDER = './files'
    UPLOAD_FOLDER = '/root/web-app/files'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mpeg', 'doc', 'docx', 'bin'}
    CELERY_CONFIG = {'broker_url': os.getenv('REDIS_URL'), 'result_backend': os.getenv('REDIS_URL')}
    LOCAL_IP = os.getenv('LOCAL_IP')
    CORS_ALLOWED_ORIGINS = ['http://kankitsuuu.fun']
    REMOTE_SERVER_PASSWORD = os.getenv('REMOTE_SERVER_PASSWORD')


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:jarsq2104@localhost:5432/servers_network'
    CELERY_CONFIG = {'broker_url': 'redis://localhost', 'result_backend': 'redis://localhost'}
    LOCAL_IP = '127.0.0.1'


class TestingConfig(Config):
    TESTING = True
