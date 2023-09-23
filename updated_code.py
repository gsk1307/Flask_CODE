from flask import *  
from flask_mail import *  
from random import *
from pytube import YouTube
from pathlib import Path
import urllib.request
import pymysql
import os
import re
import ipaddress
import requests
from werkzeug.utils import secure_filename
import pika, os
import uuid
import datetime

app=Flask(__name__)
mail = Mail(app)
app.secret_key = 'sai.chaitu1307@gmail.com'

app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465     
app.config["MAIL_USERNAME"] = 'sai.chaitu1307@gmail.com'  
app.config['MAIL_PASSWORD'] = 'jmnmmhnoyxrcymkw'  
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


def db_connection():
    timeout = 10
    connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="defaultdb",
    host="mysql-1ed7bbbc-wlmycn-2bde.aivencloud.com",
    password="AVNS_bgJrNel49GgbukSs-4U",
    read_timeout=timeout,
    port=26098,
    user="avnadmin",
    write_timeout=timeout,
    )
    return connection

def rabbitdq_connection():
		url = os.environ.get('CLOUDAMQP_URL', 'amqps://qkccwucm:ewRM2mVltak6bckNsUnQwRGl1IStk-I2@puffin.rmq2.cloudamqp.com/qkccwucm')
		params = pika.URLParameters(url)
		connection1 = pika.BlockingConnection(params)
		return connection1

		

@app.route('/validate', methods=['POST'])
def validate_otp(email, otp):
		email = request.form['email']
		otp = request.form['otp']
		connection = db_connection()
		connection_cursor = connection.cursor()
		query = f"SELECT * from Email where email = '{email}' and otp = '{otp}'"
		connection_cursor.execute(query)
		users=connection_cursor.fetchall()
		print(len(users))
		if len(users)>0:
			return True
		else:
			return False
		
	
@app.route('/', methods=['GET','POST'])
def login():
	if request.method == 'GET':
		if 'user_id' in session:
			return redirect(url_for('profile'))
		else:
			return render_template('login.html',message="")
	elif request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		query = f"SELECT * from Email where username = '{username}' and passwrd = '{password}';"
		connection = db_connection()
		connection_cursor = connection.cursor()
		connection_cursor.execute(query)
		user = connection_cursor.fetchone()
		print("===================================================")
		print(user)
		if user is not None:
			if user['username']==username and user['passwrd']==password:
				session['user_id'] = user['personid']
				print("--------------------")
				print(session['user_id'])
				return redirect(url_for('profile'))
			
			
		else:
			message="user not found"
			return render_template('login.html',message=message)

@app.route('/profile')
def profile():
	if 'user_id' in session:
		connection = db_connection()
		connection_cursor = connection.cursor()
		user_id = session['user_id']
		query=f"SELECT * FROM Email WHERE personid = {user_id}"
		connection_cursor.execute(query)
		users=connection_cursor.fetchone()
		print(users)
	
		return render_template("profile.html",users=users)
	else:
		message="You must be logged in"
		return render_template('login.html',message=message)
		
@app.route('/register', methods=['GET', 'POST'])
def register():
		message=" "
		if request.method == 'GET':
			print("Get Register")
			return render_template('register.html', message="please fill out the form")
		elif request.method == 'POST':

			print(request.form)
			if 'verify' in request.form:
				email = request.form['email']
				otp_req = request.form['otp']
				print(otp)
				print(email)
				if validate_otp(email, otp_req):
					return render_template("login.html", message="Successfully Verified... Please Login.")
				else:
					return render_template("verify.html")
				
			if 'register' in request.form:
				phonenum=request.form['phonenum']
				password = request.form['password']
				email = request.form['email']
				username = request.form['username']
				query= f"SELECT * from Email where email = '{email}';"
				connection = db_connection()
				connection_cursor = connection.cursor()
				connection_cursor.execute(query)
				users=connection_cursor.fetchall()
				print(len(users))
				if len(users)>0:
					message = "The email address already exists"
					connection_cursor.close()
					connection.close()
					return render_template('register.html', message=message)
				else:
					otp=randint(000000,999999)
					print(otp)
					validation = 0
					query= f"INSERT INTO Email (username,email,passwrd,phonenum,otp) VALUES ('{username}','{email}', '{password}','{phonenum}','{otp}');"
					print(query)
					connection_cursor.execute(query)
					connection.commit()
					connection_cursor.close()
					connection.close()
					message='Registration successful'
					msg = Message(subject='OTP',sender ='sai.chaitu1307@gmail.com',recipients = [email] )
					msg.body = str(otp)
					mail.send(msg)
					return render_template('verify.html', message=message, email=email)
			else:
				message = "Please enter an email address"
			return render_template('register.html')
		
@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp','mp4'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/gallery', methods=['POST','GET'])
def gallery():
	if request.method == 'GET':
		if 'user_id'in session:
			user_id=session.get('user_id')
			connection = db_connection()
			connection_cursor = connection.cursor()
			query = f" SELECT  user_id,filename from pic_info  WHERE user_id='{user_id}';"
			print(query)
			connection_cursor.execute(query)
			images = connection_cursor.fetchall()
			print(f"Total images information ---->{images}")
			connection_cursor.close()
			connection.close()
		return render_template('gallery.html',images=images)
	if request.method == 'POST':
		if 'user_id' in session and 'files' in request.files:
			files=request.files.getlist('files')
			print("--------------------------------------------")
			print(type(files))
			user_id=session['user_id']
			print(user_id)
			path = os.getcwd()
			print(f"path----->{path}")
			UPLOAD_FOLDER = os.path.join(path, 'uploads')
			print("this is upload folder --->" ,UPLOAD_FOLDER)
			for file in files:
				if file and allowed_file(file.filename):
							filename = secure_filename(file.filename)
							print(f"actual filename------>{filename}")
							os.makedirs(os.path.dirname(f"uploads/{user_id}/{filename}"), exist_ok=True)
							app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
							print("+++++++", UPLOAD_FOLDER)
							file.save(os.path.join(f"{app.config['UPLOAD_FOLDER']}/{user_id}", file.filename))
							print("-----------------------------------")
							connection = db_connection()
							connection_cursor = connection.cursor()
							query = f"INSERT INTO pic_info (user_id,filename) VALUE ('{user_id}', '{filename}');"
							print(query)
							connection_cursor.execute(query)
							connection.commit()
							connection_cursor.close()
							connection.close()
			return redirect(url_for('gallery'))

@app.route('/uploads/<user_id>/<filename>',methods=["GET"])
def uploads(user_id, filename):
	session_user_id=session.get('user_id')
	if session_user_id is not None:
		print(user_id )
		if filename.lower().endswith(('mp4')):
			return send_file(f"uploads/{user_id}/{filename}")
		elif filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
			return send_file(f"uploads/{user_id}/{filename}")
        # else:
        #     return "Forbidden", 403


@app.route('/videos', methods=['POST','GET'])
def videos():
	if request.method == 'GET':
		if 'user_id'in session:
			user_id=session.get('user_id')
			connection = db_connection()
			connection_cursor = connection.cursor()
			query = f" SELECT  user_id,filename from video_info  WHERE user_id='{user_id}';"
			print(query)
			connection_cursor.execute(query)
			videos = connection_cursor.fetchall()
			print(f"Total videos information ---->{videos}")
			connection_cursor.close()
			connection.close() 
		return render_template('videos.html',videos=videos)
	if request.method == 'POST':
		if 'user_id' in session and 'files' in request.files:
			files=request.files.getlist('files')
			print("--------------------------------------------")
			print(type(files))
			user_id=session['user_id']
			print(user_id)
			path = os.getcwd()
			print(f"path----->{path}")
			UPLOAD_FOLDER = os.path.join(path, 'uploads')
			for file in files:
				if file and allowed_file(file.filename):
							filename = secure_filename(file.filename)
							print(f"actual filename------>{filename}")
							os.makedirs(os.path.dirname(f"uploads/{user_id}/{filename}"), exist_ok=True)
							app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
							file.save(os.path.join(f"{app.config['UPLOAD_FOLDER']}/{user_id}",filename))
							print("-----------------------------------")
							connection = db_connection()
							connection_cursor = connection.cursor()
							query = f"INSERT INTO video_info (user_id,filename) VALUE ('{user_id}', '{filename}');"
							print(query)
							connection_cursor.execute(query)
							connection.commit()
							connection_cursor.close()
							connection.close()
			return redirect(url_for('videos'))


@app.route('/delete/<int:user_id>/<filename>', methods=['POST'])
def delete_image(user_id,filename):
	session_user_id = session.get('user_id')
	if session_user_id is not None and str(session_user_id) == str(user_id):
		print(f"it is in deleting with userid {session_user_id}")
		path_to_delete = os.path.join('uploads', str(user_id), filename)
		print(f"path_to_delete---->{path_to_delete}")
		if os.path.exists(path_to_delete):
			os.remove(path_to_delete)
			print(f"After delete--->{path_to_delete}")
			connection = db_connection()
			connection_cursor = connection.cursor()
			query = f"DELETE FROM pic_info WHERE user_id='{user_id}' AND filename='{filename}';"
			connection_cursor.execute(query)
			connection.commit()
			connection_cursor.close()
			connection.close()
			return redirect(url_for('gallery'))
		else:
			print("---------------------------------")
			return "Forbidden", 403

@app.route('/delete_video/<int:user_id>/<filename>', methods=['POST'])
def delete_video(user_id,filename):
	session_user_id = session.get('user_id')
	if session_user_id is not None and str(session_user_id) == str(user_id):
		print(f"it is in deleting with userid {session_user_id}")
		path_to_delete = os.path.join('uploads', str(user_id), filename)
		print(f"path_to_delete---->{path_to_delete}")
		if os.path.exists(path_to_delete):
			os.remove(path_to_delete)
			print(f"After delete--->{path_to_delete}")
			connection = db_connection()
			connection_cursor = connection.cursor()
			query2 = f"DELETE FROM video_info WHERE user_id='{user_id}' AND filename='{filename}';"
			print("--------------")
			connection_cursor.execute(query2)
			connection.commit()
			connection_cursor.close()
			connection.close()
			return redirect(url_for('videos'))
		else:
			print("---------------------------------")
			return "Forbidden", 403
		
@app.route('/editprofile',methods=["POST","GET"])
def editprofile():  
            if 'user_id' in session:
                user_id=session.get('user_id')
                if request.method=='GET':
                    connection = db_connection()
                    connection_cursor = connection.cursor()
                    query=f"SELECT * FROM Email WHERE personid ='{user_id}';"
                    connection_cursor.execute(query)
                    print(f"----------->{query}")
                    user=connection_cursor.fetchone()
                    connection.close()
                    return render_template('editprofile.html',user=user)

                if request.method=="POST":
                    new_username=request.form['username']
                    new_email=request.form['email']
                    new_phonenum=request.form['phonenum']
                    connection = db_connection()
                    connection_cursor = connection.cursor()
                    query=f"UPDATE Email SET username='{new_username}', email='{new_email}', phonenum='{new_phonenum}' WHERE personid='{user_id}';"
                    connection_cursor.execute(query)
                    print(query)
                    connection.commit()
                    connection_cursor.close()
                    connection.close()
                    return redirect(url_for('profile',user_id=user_id))
            return "forbidden"



@app.route("/bulkdownload", methods=["GET","POST"])
def bulkdownload():      
	mesage = ''
	errorType = 0
	if request.method == 'POST' and 'video_url' in request.form:
		youtubeUrls = request.form.get("video_url")
		youtubeUrls = youtubeUrls.split("\n")

		db_conn = db_connection()
		db_cursor = db_conn.cursor()
		rmq_conn = rabbitdq_connection()
		rmq_channel = rmq_conn.channel()
		rmq_channel.queue_declare(queue="youtube_download_queue", durable=True)

		user_id = session['user_id']		
		timestamp = datetime.datetime.now()
		status="queued"

		for url in youtubeUrls:
			id = uuid.uuid1()
			query2=f"INSERT INTO youtube_url (job_id,job_url,user_id,time_stamp,job_status) VALUES ('{id}', '{url}','{user_id}','{timestamp}','{status}');"
			db_cursor.execute(query2)
			db_conn.commit()

			payload={
				"job_id": {str(id)},
				"job_url": {url},
				"user_id": {user_id},
				"timestamp": {str(timestamp)}
			}
			print(payload)
			rmq_channel.basic_publish(body=str(payload), exchange="", routing_key="youtube_download_queue")

		mesage = 'Video Downloaded and Added to Your Profile Successfully!'
		errorType = 1
		db_conn.close()
		db_cursor.close()
		rmq_channel.close()
		rmq_conn.close()

	return render_template('bulkdownload.html', mesage = mesage, errorType = errorType)

# @app.route('/bulkdownload')
# def bulkdownload():
# 	if request.method == 'POST' and 'video_url' in request.form:
# 		youtubeUrl = request.form["video_url"]
# 		print(youtubeUrl)
# 		return "successssssss"
		# if(youtubeUrl):
		# 	validateVideoUrl = (r'(https?://)?(www\.)?''(youtube|youtu|youtube-nocookie)\.(com|be)/''(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
		# 	validVideoUrl = re.match(validateVideoUrl, youtubeUrl)
		# 	if validVideoUrl:
		# 		return "Vishnu"





@app.route('/location')
def get_location():
    return render_template('location.html')

@app.route('/iplocation', methods=["GET","POST"])
def post_geolocation():
	if request.method == 'GET':
		return render_template('index2.html')
	elif request.method == 'POST':
		ipaddress.ip_address(request.form['ip_address'])
		req = requests.get('https://ipgeolocation.abstractapi.com/v1/?ip_address=' + request.form['ip_address'] + '&api_key=2470d093773e499ea714dc1c5c1c598e')
		return make_response(jsonify(req.json()))
	
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
		if request.method == 'POST':
			email = request.form['email']
			otp = str(randint(100000, 999999))
			msg = Message(subject='Forgot Password OTP', sender='sai.chaitu1307@gmail.com', recipients=[email])
			msg.body = f'Your OTP for resetting the password is: {otp}'
			mail.send(msg)
			# Store the OTP in the session to verify later
			session['reset_password_otp'] = otp
			print("session opt is ====",otp)
			session['reset_password_email'] = email
			return redirect(url_for('verify_otp'))
		return render_template('forgot_password.html')

# Route for verifying OTP and setting a new password
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
		if request.method == 'POST':
			entered_otp = request.form['otp']
			new_password = request.form['new_password']
			print("entered otp ::::::::",entered_otp)
			if 'reset_password_otp' in session and 'reset_password_email' in session:
				if entered_otp == session['reset_password_otp']:
					# Update the user's password in the database
					email = session['reset_password_email']
					connection = db_connection()
					connection_cursor = connection.cursor()
					query = f"UPDATE Email SET passwrd = '{new_password}' WHERE email = '{email}';"
					print("query is >>>>",query)
					connection_cursor.execute(query)
					connection.commit()
					connection_cursor.close()
					connection.close()
					return redirect(url_for('login'))
				else:
					flash('Incorrect OTP. Please try again.')
			else:
				flash('OTP session expired. Please request a new OTP.')
		return render_template('verify_otp.html')
		
    
		
			

if __name__=="__main__":
	app.run(debug= True)
