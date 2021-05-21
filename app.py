from flask import Flask, request , render_template,redirect,url_for,flash
import os
import mysql.connector as sqlConnect
import matplotlib.pyplot as plt
from datetime import date,datetime

app=Flask(__name__)
app.config['SECRET_KEY']='2b293a243de5cb3f6d6e4eb4a0b526fa'

image_folder=folder=os.path.join('static/images')
app.config['image']=image_folder

css_folder=folder=os.path.join('static/style')
app.config['css']=css_folder
app.config['curr_name']=""

doc_folder=folder=os.path.join('static/Case_Documents')
app.config['documents']=doc_folder



@app.route("/login",methods=['GET','POST'])
def login():

	image1=os.path.join(app.config['image'],'lawyerloginphoto.png')
	image2=os.path.join(app.config['image'],'Logo_image.svg')
	if(request.method=="POST"):
		email=request.form.get("email")
		password=request.form.get("pass")
		print("Input Received")
		val=checkCredentials(email,password)
		if(val):
			print("Success")
			database=Connect()
			cursor=database.cursor()
			query='select person_id ,first_name ,email, password from person where email = "'+ str(email) + '" and password = "' + str(password)+'";'
			cursor.execute(query)
			person_id=""
			for x in cursor:
				person_id=x[0]
			database.close()
			if(checkLawyer(person_id)):
				add_login_stats(person_id)
				return redirect(url_for('lawyer',person_id=person_id))
			else:
				print("Failure")
				flash('Sorry Currently we are only open for Lawyers','failure')
			

		else:
			print("Failure")
			flash('Incorrect Password or Email','failure')
			return redirect(url_for('login'))
	return render_template('login.html',image1=image1,image2=image2)


@app.route("/lawyer/<person_id>")
@app.route("/lawyer/profile/<person_id>")
def lawyer(person_id):
	
	database=Connect()
	cursor=database.cursor()
	query='select * from person where person_id = ' + str(person_id)
	query1='select T4.bar_council_number, T4.wins, T4.loss, T4.activecases,T3.category from (select T1.bar_council_number, T1.Category from lawyer as t1, person as t2 where t1.person_id = t2.person_id and t2.person_id = '+str(person_id)+') as T3, lawyer_stats as T4 where T3.bar_council_number=T4.bar_council_number'
	query=query.lower()
	query1=query.lower()
	cursor.execute(query)
	person_details = " "
	person_stats=""
	for x in cursor:
		person_details=x
	cursor.execute(query1)
	for x in cursor:
		person_stats=x
	name=person_details[1]
	arr=[]
	arr.insert(0,person_details)
	arr1=[]
	arr1.insert(0,person_stats)
	database.close()
	return render_template('lawyer.html',name=name,person_details=arr,person_stats=arr1,id=person_id)


@app.route("/laywer/case/<person_id>")
def lawyercases(person_id):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select * from person where person_id = ' + str(person_id)
	cursor.execute(query)
	person_details=""
	for x in cursor:
		person_details=x
	name=person_details[1]
	arr=getCaseDetails(person_id)
	database.close()
	return render_template('lawyercases.html',name=name,id=person_id,casedetails=arr)

@app.route("/lawyer/upload/<person_id>",methods=['POST','GET'])
def lawyerupload(person_id):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select * from person where person_id = ' + str(person_id)
	cursor.execute(query)
	person_details=""
	for x in cursor:
		person_details=x
	name=person_details[1]
	database.close()
	if(request.method=="POST"):
		case_id=request.form.get('caseid')
		document_type=request.form.get('document_type')
		file=request.files['inputfile']
		if(not(file)):
			print("Failure")
			flash('No file selected, please select a file','failure')
		else:
			val=checkForFile(person_id,case_id)
			if(val):
				number=getDocNumber()
				file_split=os.path.splitext(file.filename)
				file_name=str(number)+file_split[1]
				add_document(number,case_id,document_type)
				file.save(os.path.join(app.config['documents'],file_name))
				print("Success")
				flash('File Uploaded Succesfully','success')
			else:
				print("Failure")
				flash('Action Not Allowed','failure')
			
		return redirect(url_for('lawyerupload',person_id=person_id))

	return render_template('lawyerupload.html',name=name,id=person_id)


@app.route("/lawyer/schedule/<person_id>",methods=['POST','GET'])
def lawyerschedule(person_id):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select * from person where person_id = ' + str(person_id)
	cursor.execute(query)
	person_details=""
	schedule=[]
	for x in cursor:
		person_details=x
	name=person_details[1]
	if(request.method=='POST'):
		days=request.form.get('days')
		print(days)
		arr=getSchedule(person_id,days)
		schedule=arr
		database.close()
		return render_template('lawyerschedule.html',name=name,id=person_id,schedule=schedule)
	database.close()
	return render_template('lawyerschedule.html',name=name,id=person_id,schedule=[])

@app.route("/lawyer/compete/<person_id>",methods=['POST','GET'])
def compete(person_id):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select * from person where person_id = ' + str(person_id)
	cursor.execute(query)
	query1='select bar_council_number from lawyer where person_id = ' + str(person_id)
	bar_number=""
	person_details=""
	name=""
	for x in cursor:
		person_details=x
	cursor.execute(query1)
	for x in cursor:
		bar_number=x[0]
	name=person_details[1]
	ranks=getStandings()
	curr=[]
	data=''
	for x in ranks:
		if(x[1]==bar_number):
			curr.append(x)
	database.close()
	return render_template('compete.html',name=name,id=person_id,standings=ranks,curr=curr)

@app.route("/")
@app.route("/about")
def about():

	for filename in os.listdir('static/images/'):
		if filename.startswith('graph_'):  
			os.remove('static/images/' + filename)

	createGraph()
	image1=os.path.join(app.config['image'],'aboutus2.png')
	image2=os.path.join(app.config['image'],'Logo_image.svg')
	image3=os.path.join(app.config['image'],'graph_active.png')
	image4=os.path.join(app.config['image'],'graph_completed.png')
	css=os.path.join(app.config['css'],'styles.css')
	arr=getCases()
	return render_template("about.html",image1=image1,css=css,image2=image2,active=arr[0],completed=arr[1],image3=image3,image4=image4)

@app.route("/user")
def user():
	return render_template('user.html')

def Connect():
	#database=sqlConnect.connect(user='root',password='1234',host='127.0.0.1',database='lawmanagement')
	database=sqlConnect.connect(user='uuaexgk1nowdesxa',password='JATiFJoPE2UN92q5ckXz',host='brkzvuwrc5wz0n5xw0np-mysql.services.clever-cloud.com',database='brkzvuwrc5wz0n5xw0np')
	return database

def checkCredentials(email,password):
	database=Connect()
	cursor=database.cursor()
	query='select email, password from person where email = "'+ str(email) + '" and password = "' + str(password)+'";'
	cursor.execute(query)
	arr=[]
	for x in cursor:
		arr.append(x)
	database.close()
	if(len(arr)>0):
		return True
	else:
		return False

def checkLawyer(person_id):
	database=Connect()
	cursor=database.cursor()
	query='select * from lawyer where person_id = ' + str(person_id)
	cursor.execute(query)
	arr=[]
	for x in cursor:
		arr.append(x)
	database.close()
	if(len(arr)>0):
		return True
	else:
		return False

def getCases():

	database=Connect()
	cursor=database.cursor()
	query='select count(*) from _case where _Status="Active"'
	arr=[]
	cursor.execute(query)
	for x in cursor:
		arr.append(x[0])
	query='select count(*) from _case where _Status="Completed"'
	cursor.execute(query)
	for x in cursor:
		arr.append(x[0])
	database.close()
	return arr

def createGraph():
	database=Connect()
	cursor=database.cursor()
	query='select T1.Charges, count(*) from (select * from _case where _status="Active") as T2 inner join accused as T1 on (T2.Case_ID = T1.Case_ID) group by T1.charges'
	count=[]
	labels=[]
	cursor.execute(query)
	for x in cursor:
	    count.append(x[1])
	    labels.append(x[0])
	plt.bar(labels,count,width=0.5)
	plt.xlabel("Crime Category")
	plt.title("Active Cases")
	plt.rcParams['figure.figsize'] = [1, 1]
	plt.ylabel("Count")
	plt.xticks(rotation=90)
	plt.savefig("static\\images\\graph_active.png",bbox_inches='tight')

	query='select T1.Charges, count(*) from (select * from _case where _status="Completed") as T2 inner join accused as T1 on (T2.Case_ID = T1.Case_ID) group by T1.charges'
	count=[]
	labels=[]
	cursor.execute(query)
	for x in cursor:
	    count.append(x[1])
	    labels.append(x[0])
	plt.bar(labels,count,width=0.5)
	plt.xlabel("Crime Category")
	plt.title("Completed Cases")
	plt.ylabel("Count")
	plt.rcParams['figure.figsize'] = [1, 1]
	plt.xticks(rotation=90)
	plt.savefig("static\\images\\graph_completed.png",bbox_inches='tight')
	database.close()


def getCaseDetails(person_id):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query1='select bar_council_number from lawyer where person_id = '+str(person_id)
	cursor.execute(query1)
	bar_number=""
	for x in cursor:
	    bar_number=x[0]
	query2='select * from fights where bar_council_number = ' + str(bar_number)
	cursor.execute(query2)
	case_id=[]
	for x in cursor:
	    case_id.append(x[1])
	accused=[]
	charges=[]
	police=[]
	judges=[]
	court=[]
	status=[]
	for _id in case_id:
	    curr_judge=""
	    query3='select * from _case where case_id = ' +str(_id)
	    cursor.execute(query3)
	    for x in cursor:
	        status.append(x[1])
	        judges.append(x[2])
	        curr_judge=x[2]
	    query4='select * from accused where case_id = ' + str(_id)
	    cursor.execute(query4)
	    for x in cursor:
	        accused.append(x[0])
	        charges.append(x[2])
	    query5='select * from judge where Judge_bar_council_number = ' + str(curr_judge)
	    cursor.execute(query5)
	    for x in cursor:
	        court.append(x[2])
	    query6='select * from investigates where case_id = ' + str(_id) + ' limit 1'
	    cursor.execute(query6)
	    for x in cursor:
	        police.append(x[1])
	cases=[]
	for x in range(len(case_id)):
		cases.append((case_id[x],status[x],accused[x],charges[x],police[x],judges[x],court[x]))

	database.close()

	return cases	

def checkForFile(person_id,caseid):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select bar_council_number from lawyer where person_id = ' + str(person_id)
	bar_number=''
	cursor.execute(query)
	for x in cursor:
		bar_number=x[0]
	query1='select * from fights where bar_council_number = ' + str(bar_number) +' and case_id = ' + str(caseid)
	cursor.execute(query1)
	arr=[]
	for x in cursor:
		arr.append(x)
	if(len(arr)>0):
		database.close()
		return True
	else:
		database.close()
		return False
def getDocNumber():
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select count(*) from documents'
	count=0
	cursor.execute(query)
	for x in cursor:
		count=x[0]
	database.close()
	return count+1

def getSchedule(person_id,days):
	database=Connect()
	cursor=database.cursor(buffered=True)
	query='select bar_council_number from lawyer where person_id = ' + str(person_id)
	cursor.execute(query)
	bar_number=''
	for x in cursor:
	    bar_number=x[0]
	query1=' ( select case_id from fights where bar_council_number = ' + str(bar_number) + ') '
	query1=query1.lower()
	query2=''
	if(not(days)):
		query2='select T1.Case_ID, T2._date,T2.Start_Time,T2.End_Time from' +  query1 + ' as T1, hearing_schedule as T2 where T1.case_id=t2.case_id and T2._date  between CURDATE() and DATE_ADD(CURDATE(), INTERVAL 10 DAY) '
	else:
		query2='select T1.Case_ID, T2._date,T2.Start_Time,T2.End_Time from' +  query1 + ' as T1, hearing_schedule as T2 where T1.case_id=t2.case_id and T2._date  between CURDATE() and DATE_ADD(CURDATE(), INTERVAL ' + days +' DAY) '
	query2=query2.lower()
	cursor.execute(query2)
	arr=[]
	for x in cursor:
		arr.append((x[0],x[1],x[2],x[3]))
	
	database.close()
	return arr

def add_login_stats(person_id):
	database=Connect()
	cursor=database.cursor()
	data = date.today()
	data= data.strftime("%Y-%m-%d")
	time=datetime.now()
	time=time.strftime("%H:%M:%S")
	cursor.execute('Insert into login_stats values(%s,%s,%s)',(person_id,str(data),str(time)))
	database.commit()
	database.close()

def add_document(number,caseid,document_type):
	database=Connect()
	cursor=database.cursor(buffered=True)
	data=date.today()
	data=data.strftime("%Y-%m-%d")
	print(caseid,document_type,number)
	cursor.execute('Insert into documents values(%s,%s,%s,%s)',(str(number),str(document_type),str(data),caseid))
	database.commit()
	database.close()

def getStandings():
	database=Connect()
	cursor=database.cursor(buffered=True)
	query1="with Result as ( select T1.bar_council_number,(T2.WINS/T2.loss) as Ratio, T2.wins, T2.loss from lawyer as T1 inner join lawyer_stats as T2 on T1.bar_council_number=T2.bar_council_number order by ratio desc ) "
	query2=" select rank() over (order by result.ratio desc) as Rankings, result.bar_council_number , result.ratio,avg(result.ratio) over ( order by result.ratio rows between unbounded preceding and unbounded following) as AverageRatio ,  result.wins, avg(result.wins) over ( rows between unbounded preceding and unbounded following) as AverageWins,  result.loss, avg(result.loss) over  ( rows between unbounded preceding and unbounded following ) as averageloss from result "
	query1=query1.lower()
	query2=query2.lower()
	query=query1 + query2
	cursor.execute(query)
	arr=[]
	for x in cursor:
		arr.append(x)
	database.close()
	return arr

if __name__ == '__main__':
	app.run(debug=True)
	