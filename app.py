from datetime import datetime
import hashlib
import time
from io import BytesIO
import paramiko
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from UserLogin import UserLogin
from config import DevelopmentConfig, ProductionConfig
import requests
from forms import LoginForm
from celery_utils import make_celery
from celery import shared_task
from flask_cors import CORS
from geolocation import get_location_by_url, get_distance

app = Flask(__name__)
app.config.from_object(ProductionConfig)
celery = make_celery(app)
celery.set_default()
cors = CORS(app, resources={
    r'/*': {'origins': app.config['CORS_ALLOWED_ORIGINS']}
})

from models import Users, Files, Servers, Replications, db, Actions

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Login to view closed pages'
login_manager.login_message_category = 'success'

local_ip = app.config['LOCAL_IP']


# celery tasks
@shared_task(ignore_result=False)
def make_replications(filename, upload: bool):
    servers = [server[0].ip for server in db.session.execute(db.select(Servers).where(Servers.ip != local_ip))]
    for server in servers:
        if upload is True:
            send_file_sftp(server, filename)
        else:
            remove_file_sftp(server, filename)
    return 'Success'


@shared_task(ignore_result=False)
def register_action(action_type, action_time, username, duration):
    try:
        server = Servers.query.filter_by(ip=local_ip).first()
        new_action = Actions(
            server=server.id,
            username=username,
            duration=duration,
            action_time=action_time,
            action_type=action_type
        )
        db.session.add(new_action)
        db.session.flush()
        message = 'Success'
    except Exception as e:
        print('DB error')
        print(e)
        db.session.rollback()
        message = 'Failure'
    db.session.commit()
    return message


@login_manager.user_loader
def load_user(user_id):
    print(f'Loading user with id: {user_id}')
    return UserLogin().get_from_db(user_id, Users)


@app.route('/')
def home():
    return redirect(url_for('get_files', page=1))


@app.route('/files/<int:page>', methods=['GET', 'POST'])
def get_files(page: int = 1):
    upload_vps = Servers.query.filter_by(ip=local_ip).first()
    files = Files.query.order_by(Files.upload_time.desc()).paginate(page=page, per_page=8, error_out=True, count=True)
    return render_template('files.html', files=files, server=upload_vps)


@app.route('/locations/choose', methods=['POST'])
def choose_upload_location():
    data = request.json
    file_location = get_location_by_url(data['url'])
    if not file_location:
        return jsonify({'server': None})
    servers = {server.ip: get_distance((server.latitude, server.longitude), file_location) for server in Servers.query.all()}
    nearest = min(servers, key=lambda key: servers[key])
    return jsonify({
        'server': nearest,
        'distance': servers[nearest],
        'url': data['url'],
        'username': current_user.username
    })


@app.route('/files/upload', methods=['POST'])
def upload_file():
    success = False
    message, message_type = 'Default', 'default'
    try:
        data = request.json
        start = time.monotonic()
        upload_vps = Servers.query.filter_by(ip=local_ip).first()
        link = data['url']
        filename = link.split('/')[-1]
        if verify_filename(filename):
            filename = secure_filename(filename)
            file_type = filename.split('.')[-1].lower()
            name = set_unique_filename('.'.join(filename.split('.')[0:-1]))
            # Проверяем уникальность имени файла (в случае совпадения добавляем префикс)
            filename = '.'.join((name, file_type))
            print(filename)
            url = hashlib.sha256(filename.encode()).hexdigest()
            with requests.get(url=link, stream=True) as response:
                if response.status_code != 200:
                    raise ValueError

                with open(f'{app.config["LOCAL_FOLDER"]}/{filename}', 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file.write(chunk)

                # add file info to db
                date = datetime.utcnow()
                user = Users.query.filter_by(username=data['username']).first()
                try:
                    new_file = Files(
                        url=url,
                        name=name,
                        file_type=file_type,
                        user_id=user.id,
                        upload_vps=upload_vps.id,
                        upload_time=date
                    )
                    db.session.add(new_file)
                    db.session.flush()
                    time_diff = f'{(time.monotonic() - start):.2f}'
                    message, message_type = f'Uploaded on VPS{upload_vps.id} {upload_vps.country}, {upload_vps.city}' \
                              f'{upload_vps.ip}\nUpload_time: {date.strftime("%y-%m-%d %H:%M:%S")}' \
                              f' Duration: {time_diff} sec\n', 'success'
                    success = True
                    register_action.delay('Upload', date, user.username, time_diff)
                    make_replications.delay(filename, True)
                except Exception as e:
                    os.remove(f"{app.config['LOCAL_FOLDER']}/{filename}")
                    db.session.rollback()
                    message, message_type = 'Database error', 'error'
                    print(e)
        else:
            message, message_type = 'Invalid filename!', 'error'
    except FileNotFoundError:
        message, message_type = 'Download file error!', 'error'
    except ValueError:
        message, message_type = 'Invalid download URL!', 'error'
    except:
        message, message_type = 'File preparation error!', 'error'
    db.session.commit()
    return jsonify({
        'success': success,
        'message': message,
        'message_type': message_type,
        'from_server': local_ip
    })


@app.route('/replications/<int:page>')
@login_required
def get_replications(page: int = 1):
    upload_vps = Servers.query.filter_by(ip=local_ip).first()
    replications = Replications.query.order_by(Replications.action_time.desc()).paginate(page=page,
                                                                                         per_page=8,
                                                                                         error_out=True,
                                                                                         count=True)
    return render_template('replications.html', replications=replications, server=upload_vps)


@app.route('/actions/<int:page>')
@login_required
def get_actions(page: int = 1):
    upload_vps = Servers.query.filter_by(ip=local_ip).first()
    actions = Actions.query.order_by(Actions.action_time.desc()).paginate(page=page,
                                                                          per_page=8,
                                                                          error_out=True,
                                                                          count=True)
    return render_template('actions.html', actions=actions, server=upload_vps)


@app.route('/download/<file_url>')
def download(file_url):
    start = time.monotonic()
    try:
        file = Files.query.filter_by(url=file_url).first()
        filename = file.name + '.' + file.file_type
        with open(f"{app.config['LOCAL_FOLDER']}/{filename}", 'rb') as file:
            data = file.read()
    except FileNotFoundError as e:
        print(e)
        flash('Replication of this file is not yet complete. Wait a bit.', 'error')
        return redirect(url_for('get_files', page=1))
    except Exception as e:
        print(e)
        flash("Download file error", "error")
        return redirect(url_for('get_files', page=1))

    time_diff = f'{(time.monotonic() - start):.2f}'
    date = datetime.utcnow()
    flash(f'VPS {local_ip}, {time_diff} sec, {date.strftime("%y-%m-%d %H:%M:%S")}')
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = 'guest'
    register_action.delay('Download', date, username, time_diff)
    return send_file(BytesIO(data), download_name=filename, as_attachment=True, max_age=0)


@app.route('/delete/<file_url>')
@login_required
def delete_file(file_url):
    try:
        start = time.monotonic()
        file = Files.query.filter_by(url=file_url).first()
        filename = file.name + '.' + file.file_type
        db.session.delete(file)
        os.remove(f"{app.config['LOCAL_FOLDER']}/{filename}")
        db.session.commit()
        flash('Successfully deleted', 'success')
        make_replications.delay(filename, False)
        time_diff = f'{(time.monotonic() - start):.2f}'
        register_action.delay('Delete', datetime.utcnow(), current_user.username, time_diff)

    except Exception as e:
        print(e)
        flash("Delete file error ", "error")
    return redirect(url_for("get_files", page=1))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_files', page=1))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("get_files", page=1))
        flash("Incorrect login/password", "error")
    return render_template("login.html", title="Login", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You logged out of the account", "success")
    return redirect(url_for('get_files', page=1))


def verify_filename(filename: str) -> bool:
    ext = filename.rsplit('.')[-1].lower()
    if ext in DevelopmentConfig.ALLOWED_EXTENSIONS:
        return True
    return False


def set_unique_filename(name: str) -> str:
    postfix = 1
    clean_name = name
    while True:
        file = Files.query.filter_by(name=clean_name).first()
        if file:
            clean_name = name + f'_{postfix}'
            postfix += 1
            continue
        return clean_name


def send_file_sftp(host, filename):
    try:
        start = time.monotonic()
        port = 22
        transport = paramiko.Transport((host, port))
        transport.connect(username='root', password=app.config['REMOTE_SERVER_PASSWORD'])
        sftp = paramiko.SFTPClient.from_transport(transport)
        remotepath = f'{app.config["UPLOAD_FOLDER"]}/{filename}'
        localpath = f'{os.path.abspath(app.config["LOCAL_FOLDER"])}/{filename}'
        print(localpath)
        sftp.put(localpath, remotepath)
        sftp.close()
        transport.close()

        try:
            time_diff = f'{(time.monotonic() - start):.2f}'
            replication = Replications(
                from_vps=Servers.query.filter_by(ip=local_ip).first().id,
                to_vps=Servers.query.filter_by(ip=host).first().id,
                action_time=datetime.utcnow(),
                action_type='Upload',
                duration=time_diff
            )
            db.session.add(replication)
            db.session.flush()
        except Exception as e:
            print('Replication DB error')
            print(e)
            sftp.remove(remotepath)
            db.session.rollback()

        db.session.commit()
        sftp.close()
        transport.close()
        print('Success')
    except Exception as e:
        print('Replication error')
        print(e)


def remove_file_sftp(host, filename):
    try:
        start = time.monotonic()
        port = 22
        transport = paramiko.Transport((host, port))
        transport.connect(username='root', password=app.config['REMOTE_SERVER_PASSWORD'])
        sftp = paramiko.SFTPClient.from_transport(transport)
        remotepath = f'{app.config["UPLOAD_FOLDER"]}/{filename}'
        sftp.remove(remotepath)
        sftp.close()
        transport.close()
        print(f'Successfully deleted from {host}')
        try:
            time_diff = f'{(time.monotonic() - start):.2f}'
            replication = Replications(
                from_vps=Servers.query.filter_by(ip=local_ip).first().id,
                to_vps=Servers.query.filter_by(ip=host).first().id,
                action_time=datetime.utcnow(),
                action_type='Delete',
                duration=time_diff
            )
            db.session.add(replication)
            db.session.flush()
        except Exception as e:
            print('Replication DB error')
            print(e)
            db.session.rollback()
    except Exception as e:
        print('Remove sftp error')
        print(e)
    db.session.commit()


