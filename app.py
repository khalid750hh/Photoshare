######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

from asyncore import read
from cmath import log
#from crypt import methods
from datetime import date, datetime
from distutils.log import Log
from email.mime import image
from encodings import utf_8
import io
from pickle import FALSE
from tkinter import E, Image
from typing import BinaryIO
from unittest import result
from xml.etree.ElementTree import Comment
from MySQLdb import Binary
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

from itsdangerous import base64_decode, base64_encode
from sqlalchemy import table

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'USERNAME'
app.config['MYSQL_DATABASE_PASSWORD'] = 'PASSWORD'
app.config['MYSQL_DATABASE_DB'] = 'photo_sharing_website'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return render_template('login.html')
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT user_password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		username=request.form.get('username')
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		birthday=request.form.get('birthday')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()

	test1 = isUsernameValid(username)
	test2 =  isEmailUnique(email)
	if (test1 and test2):
		print(cursor.execute("INSERT INTO Users (user_id, first_name, last_name, email, date_of_birth, hometown, gender, user_password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(username, firstname, lastname, email, birthday, hometown, gender, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo, photo_id, caption FROM photos WHERE album_id in (SELECT album_id FROM albums WHERE owner_id = '{0}')".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getLatestPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT photo, photo_id, caption FROM photos order by photo_id desc limit 50")
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getMostContribution(i):
	cursor = conn.cursor()
	cursor.execute("SELECT A.owner_id, count(A.owner_id) FROM photos P, Albums A where P.album_id = A.album_id group by A.owner_id ORDER BY count(A.owner_id) desc limit {0}".format(i))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserFullNameFromId(id):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM Users WHERE user_id = '{0}'".format(id))
	name = cursor.fetchone()
	name = name[0] + " " + name[1]
	return name

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def isUsernameValid(username):
	#use this to check if a email has already been registered
	if (len(username) > 3 and username.lower() != "guest"):
		cursor = conn.cursor()
		if cursor.execute("SELECT user_id  FROM Users WHERE user_id = '{0}'".format(username)):
			#this means there are greater than zero entries with that username
			return False
		else:
			return True
#end login code

def getUserLikesFromId(i):
	cursor = conn.cursor()
	cursor.execute("SELECT count(liked_id) from likes WHERE liked_id = '{0}'".format(i))
	num_likes = cursor.fetchone()
	if (num_likes == None):
		return 0
	return num_likes

def getFriendReccs(i):
	cursor = conn.cursor()
	uid = i
	friends = getUserFriendsFromId(uid)
	reccs = []
	cursor.execute("SELECT user_id FROM users WHERE user_id != '{0}'".format(uid))
	userlist = cursor.fetchall()
	for i in range(len(friends)):
		for j in range(len(userlist)):
			if(checkIfFriends(friends[i][0], userlist[j][0])):
				reccs += [userlist[j][0]]
	reccs = list(set(reccs))
	if(len(reccs)>10):
		reccs = reccs[0:10]
	return reccs

def friendsYouMayLike(uid):
	cursor = conn.cursor()
	most = getMostContribution(999)
	filtered = []
	for i in range(len(most)):
		filtered += [most[i][0]]
	filtered = list(set(filtered))
	answer = []
	for i in range(len(filtered)):
		if(checkIfFriends(uid, filtered[i]) == 0):
			answer += [filtered[i]]
	return answer

def getUserFriendsFromId(i):
	cursor = conn.cursor()
	cursor.execute("SELECT user1 FROM friends WHERE user2 = '{0}' and accepted = 1".format(i))
	friends1 = cursor.fetchall()
	cursor.execute("SELECT user2 FROM friends WHERE user1 = '{0}' and accepted = 1".format(i))
	friends2 = cursor.fetchall()
	return (friends1 + friends2)

def getUserFriendRequestsFromId(i):
	cursor = conn.cursor()
	cursor.execute("SELECT user1 FROM friends WHERE user2 = '{0}' and accepted = 0".format(i))
	friendRequests = cursor.fetchall()
	return (friendRequests)

def checkIfFriends(i1, i2):
	#returns 2 if friends, 1 if request was sent, 0 if request was recieved or no request sent or recieved
	cursor = conn.cursor()
	cursor.execute("SELECT user1, user2 FROM friends WHERE user1 = '{0}' and user2 = '{1}' and accepted = 1".format(i1, i2))
	friends1 = cursor.fetchall()
	cursor.execute("SELECT user1, user2 FROM friends WHERE user1 = '{0}' and user2 = '{1}' and accepted = 1".format(i2, i1))
	friends2 = cursor.fetchall()
	if(len(friends1)>0 or len(friends2)>0):
		return 2
	cursor.execute("SELECT user1, user2 FROM friends WHERE user1 = '{0}' and user2 = '{1}' and accepted = 0".format(i1, i2))
	friends1 = cursor.fetchall()
	if(len(friends1)>0):
		return 1
	return 0


def getUserAlbums(i):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, album_id FROM albums WHERE owner_id = '{0}'".format(i))
	albums = cursor.fetchall()
	return (albums)

@app.route('/add', methods=['POST'])
@flask_login.login_required
def add():
	friend_id = request.form.get('friend_id')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friendCheck = checkIfFriends(uid, friend_id)
	cursor = conn.cursor()
	if (friendCheck == 0):
		friendCheck2 = checkIfFriends(friend_id, uid)
		if(friendCheck2 == 0):
			cursor.execute("INSERT into friends (user1, user2, accepted) VALUES ('{0}', '{1}', '{2}')".format(uid, friend_id, 0))
			conn.commit()
		else:
			cursor.execute("UPDATE friends SET accepted = '{2}' WHERE user1 = '{1}' and user2 = '{0}'".format(uid, friend_id, 1))
			conn.commit()

	fullname = getUserFullNameFromId(uid)
	num_likes = getUserLikesFromId(uid)
	friend_requests = getUserFriendRequestsFromId(uid)
	friends = getUserFriendsFromId(uid)
	albums=getUserAlbums(uid)
	return render_template('profile.html', name=uid, friends=friends, friendReq=friend_requests, likes=num_likes, realname=fullname,albums=albums, photos=getUsersPhotos(uid), base64=base64)





@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		fullname = getUserFullNameFromId(uid)
		num_likes = getUserLikesFromId(uid)
		friend_requests = getUserFriendRequestsFromId(uid)
		friend_reccs = getFriendReccs(uid)
		friend_reccs2 = friendsYouMayLike(uid)
		friends = getUserFriendsFromId(uid)
		albums = getUserAlbums(uid)
		return render_template('profile.html', name=uid, friends=friends, friendReq=friend_requests, friend_reccs=friend_reccs, friend_reccs2=friend_reccs2, likes=num_likes, realname=fullname, albums=albums, photos=getUsersPhotos(uid), base64=base64)
	elif request.method == 'POST':
		uid = request.form.get('user_id')
		fullname = getUserFullNameFromId(uid)
		num_likes = getUserLikesFromId(uid)
		can_send_request = checkIfFriends(getUserIdFromEmail(flask_login.current_user.id), uid)
		albums = getUserAlbums(uid)
		if(can_send_request == 0 and getUserIdFromEmail(flask_login.current_user.id) != uid):
			return render_template('profile.html', name=uid, send=True, likes=num_likes, realname=fullname,albums=albums, photos=getUsersPhotos(uid), base64=base64)
		if(can_send_request == 0):
			return render_template('profile.html', name=uid, send=False, likes=num_likes, realname=fullname,albums=albums, photos=getUsersPhotos(uid), base64=base64)

		return render_template('profile.html', name=uid, likes=num_likes, realname=fullname,albums=albums, photos=getUsersPhotos(uid), base64=base64)

@app.route('/album', methods=['GET', 'POST'])
@flask_login.login_required
def albums():

	if request.method == 'POST':
		album_name = request.form.get('album_name')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("INSERT INTO albums (owner_id, album_name, date_of_creation) VALUES ('{0}', '{1}', '{2}')".format(getUserIdFromEmail(flask_login.current_user.id), album_name, datetime.now()))
		conn.commit()
		return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Album created!', photos=getUsersPhotos(uid), base64=base64)

	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('album.html', name=uid)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_id = request.form.get('album')
		photo_data =imgfile.read()
		photo_string = base64.b64encode(photo_data).decode('ascii')
		cursor = conn.cursor()
		#need to change album id in format after implementing albums properly. also might need to change photos table to include owner_id for an easier time.
		cursor.execute("INSERT INTO photos (album_id, caption, photo) VALUES ('{0}', '{1}', '{2}' )".format(album_id, caption, photo_string))
		photo_id = conn.insert_id()
		conn.commit()
		tags = request.form.get('tags')
		try:
			spli = tags.split()
			spli = list(set(spli))
			for i in range(len(tags)):
				cursor.execute("INSERT INTO tags (photo_described, word) VALUES ('{0}', '{1}')".format(photo_id, spli[i]))
				conn.commit()
		except:
			return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)

		return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT album_id, album_name FROM albums WHERE owner_id = '{0}'".format(uid))
		return render_template('upload.html', name=getUserIdFromEmail(flask_login.current_user.id), albums=cursor.fetchall())
#end photo uploading code


@app.route('/search', methods=['GET', 'POST'])
#@flask_login.login_required
def photo_search():
	if request.method == 'POST':
		search_term = request.form.get('search_space')
		option = request.form['searchtype']
		cursor = conn.cursor()
		if(option == "caption"):
			cursor.execute("SELECT photo, photo_id, caption FROM photos WHERE caption LIKE '%" + search_term + "%'")
			result = cursor.fetchall()
			try:
				if(result == ()):
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Here are the results!', photos=result, base64=base64)
			except:
				if(result == ()):
					return render_template('hello.html', message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', message='Here are the results!', photos=result, base64=base64)

		elif(option == "tags"):
			tag = search_term.split(" ")[0]
			cursor.execute("SELECT P.photo, P.photo_id, P.caption FROM photos P, tags T WHERE P.photo_id = T.photo_described and T.word = '{0}'".format(tag))
			result = cursor.fetchall()
			try:
				if(result == ()):
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Here are the results!', photos=result, base64=base64)
			except:
				if(result == ()):
					return render_template('hello.html', message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', message='Here are the results!', photos=result, base64=base64)
		elif(option == "usertags"):
			tag = search_term.split(" ")[0]
			try:
				cursor.execute("SELECT P.photo, P.photo_id, P.caption FROM photos P, tags T, Albums A WHERE P.photo_id = T.photo_described and T.word = '{0}' and A.album_id = P.photo_id and A.owner_id = '{1}'".format(tag, getUserIdFromEmail(flask_login.current_user.id)))
				result = cursor.fetchall()
				if(result == ()):
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='Here are the results!', photos=result, base64=base64)
			except:
				return render_template('hello.html', message='Not logged in... Please log in first.', photos=None, base64=base64)
		elif(option == "comments"):
			cursor.execute("SELECT owner_id, photo_id FROM comments WHERE comment_text = '{0}' and owner_id != 'guest'".format(search_term))
			result = cursor.fetchall()
			try:
				if(result == ()):
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', name=getUserIdFromEmail(flask_login.current_user.id), cont2=result, message='Here are the results!', photos=None, base64=base64)
			except:
				if(result == ()):
					return render_template('hello.html', message='No results found... Please try again.', photos=None, base64=base64)
				else:
					return render_template('hello.html', cont2=result, message='Here are the results!', photos=None, base64=base64)

	else:
		cursor = conn.cursor()
		cursor.execute("SELECT word, count(word) FROM tags GROUP BY word ORDER BY count(word) desc")
		tags = cursor.fetchall()
		try:
			return render_template('search.html', tags=tags, name=getUserIdFromEmail(flask_login.current_user.id))
		except:
			return render_template('search.html', tags=tags)

		

@app.route("/photo", methods=['GET', 'POST'])
def photo():
	if request.method == 'POST':
		photo_id=request.form.get('photo_id')
		cursor=conn.cursor()
		cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where photo_id='{0}'".format(photo_id))
		photo_info=cursor.fetchone()
		album_id=photo_info[3]
		cursor.execute("SELECT owner_id, album_name FROM albums where album_id='{0}'".format(album_id))
		album_info = cursor.fetchone()
		owner_id=album_info[0]
		album_name = album_info[1]
		cursor.execute("SELECT owner_id, comment_text, date_posted FROM comments WHERE photo_id='{0}'".format(photo_id))
		all_comments=cursor.fetchall()
		num_comments=len(all_comments)
		cursor.execute("SELECT count(liked_photo_id) FROM likes where liked_photo_id='{0}'".format(photo_id))
		likes_num = cursor.fetchone()[0]
		deletable = False
		try:
			uid = getUserIdFromEmail(flask_login.current_user.id)
			deletable = (owner_id == uid)
		except:
			deletable = False
	try:
		try:
			return render_template('photo.html',loggedin=getUserIdFromEmail(flask_login.current_user.id), name=owner_id, deletable=deletable, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)

		except:
			return render_template('photo.html', name=owner_id, deletable=deletable, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)
	except:
		latest = getLatestPhotos()
		return render_template('hello.html', message='Photo retrieval failed... Please try again later.', photos=latest, base64=base64, newest="newest")

@app.route("/comment", methods=['POST'])
def comment():
	if request.method == 'POST':
		photo_id=request.form.get('photo_id')
		comment_owner_id=request.form.get('user_id')
		comment=request.form.get('comment')
		cursor = conn.cursor()
		cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where photo_id={0}".format(photo_id))
		photo_info=cursor.fetchone()
		caption=photo_info[1]
		photo=photo_info[2]
		album_id=photo_info[3]
		cursor.execute("SELECT owner_id, album_name FROM albums where album_id={0};".format(album_id))
		album_info = cursor.fetchone()
		owner_id=album_info[0]
		album_name = album_info[1]
		cursor.execute("SELECT owner_id, comment_text, date_posted FROM comments WHERE photo_id='{0}'".format(photo_id))
		all_comments=cursor.fetchall()
		num_comments=len(all_comments)
		cursor.execute("SELECT count(liked_photo_id) FROM likes where liked_photo_id='{0}'".format(photo_id))
		likes_num = cursor.fetchone()[0]
		if(comment_owner_id == "guest" or owner_id != getUserIdFromEmail(flask_login.current_user.id)):
			cursor.execute("INSERT INTO comments (comment_text, owner_id, date_posted, photo_id) VALUES ('{0}', '{1}', '{2}', '{3}' )".format(comment, comment_owner_id, datetime.now(), photo_id))
			conn.commit()
			cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where photo_id={0}".format(photo_id))
			photo_info=cursor.fetchone()
			try:
				cursor=conn.cursor()
				cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where photo_id={0}".format(photo_id))
				photo_info=cursor.fetchone()
				caption=photo_info[1]
				photo=photo_info[2]
				album_id=photo_info[3]
				cursor.execute("SELECT owner_id, album_name FROM albums where album_id={0};".format(album_id))
				album_info = cursor.fetchone()
				owner_id=album_info[0]
				album_name = album_info[1]
				cursor.execute("SELECT owner_id, comment_text, date_posted FROM comments WHERE photo_id='{0}'".format(photo_id))
				all_comments=cursor.fetchall()
				num_comments=len(all_comments)
				cursor.execute("SELECT count(liked_photo_id) FROM likes where liked_photo_id='{0}'".format(photo_id))
				likes_num = cursor.fetchone()[0]
				
				try:
					try:
						return render_template('photo.html',loggedin=getUserIdFromEmail(flask_login.current_user.id), name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)

					except:
						return render_template('photo.html', name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)
				except:
					latest = getLatestPhotos()
					return render_template('hello.html', message='Photo retrieval failed... Please try again later.', photos=latest, base64=base64, newest="newest")

			except:
				return render_template('photo.html', name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)
		else:
			return render_template('photo.html', name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)



@app.route("/like", methods=['POST'])
@flask_login.login_required
def like():
	if request.method == 'POST':
		photo_id=request.form.get('photo_id')
		user_id=request.form.get('user_id')
		owner_id=request.form.get('owner_id')
		cursor = conn.cursor()
		cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where photo_id={0}".format(photo_id))
		photo_info=cursor.fetchone()
		caption=photo_info[1]
		photo=photo_info[2]
		album_id=photo_info[3]
		cursor.execute("SELECT liker_id, liked_photo_id FROM likes where liker_id = '{0}' and liked_photo_id = '{1}'".format(user_id, photo_id))
		exists = cursor.rowcount
		if (exists == 0):
			cursor.execute("INSERT INTO likes (liker_id, liked_id, liked_photo_id, album_id) VALUES ('{0}', '{1}', '{2}', '{3}' )".format(user_id, owner_id, photo_id, album_id))
			conn.commit()
		try:
			cursor.execute("SELECT owner_id, album_name FROM albums where album_id={0};".format(album_id))
			album_info = cursor.fetchone()
			owner_id=album_info[0]
			album_name = album_info[1]
			cursor.execute("SELECT owner_id, comment_text, date_posted FROM comments WHERE photo_id='{0}'".format(photo_id))
			all_comments=cursor.fetchall()
			num_comments=len(all_comments)
			cursor.execute("SELECT count(liked_photo_id) FROM likes where liked_photo_id='{0}'".format(photo_id))
			likes_num = cursor.fetchone()[0]
			try:
				try:
					return render_template('photo.html',loggedin=getUserIdFromEmail(flask_login.current_user.id), name=owner_id, album=album_name,num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)

				except:
					return render_template('photo.html', name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)
			except:
				latest = getLatestPhotos()
				return render_template('hello.html', message='Photo retrieval failed... Please try again later.', photos=latest, base64=base64, newest="newest")

		except:
			return render_template('photo.html', name=owner_id, album=album_name, num=num_comments, comments=all_comments, likes=likes_num, photo=photo_info, base64=base64)
		
def getAlbumPhotos(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id, caption, photo, album_id FROM photos where album_id={0}".format(album_id))
	return(cursor.fetchall())

@app.route("/album_display", methods=['POST'])
def album_display():
	album_id=request.form.get('album_id')
	album_name=request.form.get('album_name')
	owner_id=request.form.get('owner_id')
	photos = getAlbumPhotos(album_id)
	uid = getUserIdFromEmail(flask_login.current_user.id)
	deletable = (owner_id == uid)
	return render_template('album_display.html',name=owner_id, album_id=album_id, album_name=album_name, deletable=deletable, photos=photos, base64=base64)

@app.route("/album_delete", methods=['POST'])
@flask_login.login_required
def album_delete():
	album_id=request.form.get('album_id')
	album_name=request.form.get('album_name')
	owner_id=request.form.get('owner_id')
	photos = getAlbumPhotos(album_id)
	uid = getUserIdFromEmail(flask_login.current_user.id)
	deletable = (owner_id == uid)
	if(deletable):
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(album_id))
		conn.commit()
		latest = getLatestPhotos()
		mostContribution = getMostContribution(10)
		try:
			return render_template('hello.html',name=getUserIdFromEmail(flask_login.current_user.id), message='Album deleted.', photos=latest, cont=mostContribution, base64=base64, newest="newest")
		except:
			return render_template('hello.html', message='Welecome to Photoshare', photos=latest, cont=mostContribution, base64=base64, newest="newest")
	return render_template('album_display.html',name=owner_id, album_name=album_name, deletable=deletable, photos=photos, base64=base64)

@app.route("/photo_delete", methods=['POST'])
@flask_login.login_required
def photo_delete():
	photo_id=request.form.get('photo_id')
	owner_id=request.form.get('owner_id')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	deletable = (owner_id == uid)
	latest = getLatestPhotos()
	mostContribution = getMostContribution(10)
	if(deletable):
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}';".format(photo_id))
		conn.commit()
		try:
			return render_template('hello.html',name=getUserIdFromEmail(flask_login.current_user.id), message='Photo deleted.', photos=latest, cont=mostContribution, base64=base64, newest="newest")
		except:
			return render_template('hello.html', message='Welecome to Photoshare', photos=latest, cont=mostContribution, base64=base64, newest="newest")
	try:
		return render_template('hello.html',name=getUserIdFromEmail(flask_login.current_user.id), photos=latest, cont=mostContribution, base64=base64, newest="newest")
	except:
		return render_template('hello.html', message='Welecome to Photoshare', photos=latest, cont=mostContribution, base64=base64, newest="newest")

#default page
@app.route("/", methods=['GET'])
def hello():
	latest = getLatestPhotos()
	mostContribution = getMostContribution(10)
	try:
		return render_template('hello.html',name=getUserIdFromEmail(flask_login.current_user.id), message='Welecome to Photoshare', photos=latest, cont=mostContribution, base64=base64, newest="newest")
	except:
		return render_template('hello.html', message='Welecome to Photoshare', photos=latest, cont=mostContribution, base64=base64, newest="newest")
	


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
