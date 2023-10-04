from flask import Flask,redirect,url_for,render_template,request,flash,session
import mysql.connector
from flask_session import Session
from key import secretkey,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
app=Flask(__name__)
app.secret_key=secretkey
app.config['SESSION_TYPE']='filesystem'
mydb = mysql.connector.connect(host="localhost" , user='root',password='krishna',db='application')

@app.route('/')
def title():
    return render_template('title.html')


@app.route('/signup/',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username=request.form['username']
        gmail=request.form['gmail']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()
        cursor.execute('select count(*) from users where gmail=%s',[gmail] )
        count1=cursor.fetchone()
        cursor.close()
        if count==(1,):
            flash('username is already taken')
            return render_template('signup.html')
        elif count1==(1,):
            flash('mail already in use')
            return render_template('signup.html')
        data={'username':username,'gmail':gmail,'password':password}
        subject='Email confirmation'
        body=f"thank you for signig up\n \n follow the link for further steps /n{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=gmail,subject=subject,body=body)
        flash('Confirmation link send to email')
        return redirect(url_for('signin'))
    return render_template('signup.html')


@app.route('/confirm/<token>/')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secretkey)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        return'Link Expired register agian'
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('you are already registered!')
            return redirect(url_for('signin'))
        else:
            cursor.execute('insert into users(username,gmail,password) value(%s,%s,%s)',[data['username'],data['gmail'],data['password']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('signin'))


@app.route('/signin/',methods=['GET','POST'])
def signin():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()
        cursor.close()
        if count==(1,):
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('wrong user name or password')
            return render_template('signin.html')
    return render_template('signin.html')


@app.route('/forgot/',methods=['GET','POST'])
def forgot():
        if request.method=='POST':
            gmail=request.form['gmail']
            password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from users where gmail=%s',[gmail])
            count=cursor.fetchone()[0]
            if count==1:
                cursor.execute('select username from users where gmail=%s',[gmail])
                username=cursor.fetchone()[0]
                data={'username':username,'gmail':gmail,'password':password}
                subject='Password reset'
                body=f"click the following link to reset /n{url_for('reset',token=token(data),_external=True)}"
                sendmail(to=gmail,subject=subject,body=body)
                flash('link is send to mail')
                return redirect(url_for('signin'))
            else:
                cursor.close()
                flash('no account existed of that gmail')
                return render_template('forgot.html') 
        else:
            return render_template('forgot.html')

@app.route('/reset/<token>')
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secretkey)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        return'Link Expired try agian'
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('UPDATE users SET password = %s WHERE (gmail = %s)',[data['password'],data['gmail']])
        mydb.commit()
        cursor.close()
        flash('password change successfully')
        return render_template('signin.html')


@app.route('/home/')
def home():
            if session.get('user'):
                return render_template('home.html')
            else:
                return redirect(url_for('signin'))


@app.route('/logout/')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully loged out')
        return redirect(url_for('signin'))
    else:
     return redirect(url_for('signin'))


@app.route('/askquestion/')
def askquestion():
    return render_template('askquestion.html')


@app.route('/que',methods=['GET','POST'])
def askQue():
    if session.get('user'):
        if request.method=='POST':
            question=request.form['question']
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into questions(question ,username) values(%s,%s)',[question,username])
            mydb.commit()
            cursor.close()
            flash('question submit')
            return redirect(url_for('home'))
        flash('fail to upload')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('signin'))


@app.route('/question/')
def question():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from questions ORDER BY time DESC;')
        data=cursor.fetchall()
        cursor.close()
        return render_template('question.html',data=data)
    return redirect(url_for('signin')) 


@app.route('/answer/<qid>')
def answer(qid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from questions where qid=%s',[qid])
        data=cursor.fetchall()
        cursor.execute('select * from answers where question_id=%s ORDER BY created_at DESC;',[qid])
        data2=cursor.fetchall()
        cursor.close()
        return render_template('answer.html',data=data,data2=data2)
    return redirect(url_for('signin'))

@app.route('/ans/<qid>',methods=['GET','POST'])
def ans(qid):
    if session.get('user'):
        if request.method=='POST':
            answer=request.form['answer']
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into answers(answer ,username,question_id) values(%s,%s,%s)',[answer,username,qid])
            mydb.commit()
            cursor.close()
            flash('answer submit')
            return redirect(url_for('answer',qid=qid))
        flash('fail to upload')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('signin'))


@app.route('/upvote/<aid>')
def upvote(aid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        username=session.get('user')
        cursor.execute('select * from vote where user=%s AND answer_id=%s',[username,aid])
        check=cursor.fetchone()
        cursor.execute('select * from answers where id=%s',[aid])
        result=cursor.fetchall()
        qid = result[0][2]
        if check==None:
            up='1'
            cursor.execute('insert into vote(user,answer_id,voteup) values(%s,%s,%s)',[username,aid,up])
            cursor.execute('update answers set upvote=upvote+1 where id=%s',[aid])
            cursor.close()
            flash('liked the answer')
            return redirect(url_for('answer',qid=qid))
        else:
            cursor.execute('delete from vote where user=%s',[username])
            cursor.execute('update answers set upvote=upvote-1 where id=%s',[aid])
            cursor.close()
            flash('like removed')
            return redirect(url_for('answer',qid=qid))
    else:
        return redirect(url_for('signin'))

@app.route('/reply/<aid>')
def reply(aid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from answers where id=%s',[aid])
        data=cursor.fetchall()
        cursor.execute('select * from replies where answer_id=%s ORDER BY created_at DESC',[aid])
        data2=cursor.fetchall()
        cursor.close()
        return render_template('reply.html',data=data,data2=data2)
    return redirect(url_for('signin'))


@app.route('/rep/<aid>',methods=['GET','POST'])
def rep(aid):
    if session.get('user'):
        if request.method=='POST':
            reply=request.form['reply']
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into replies(reply ,username,answer_id) values(%s,%s,%s)',[reply,username,aid])
            mydb.commit()
            cursor.close()
            flash('reply submit')
            return redirect(url_for('reply',aid=aid))
        flash('fail to upload')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('signin'))


app.run(debug=True,use_reloader=True)