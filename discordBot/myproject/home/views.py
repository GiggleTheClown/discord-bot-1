from django.shortcuts import render
import mysql.connector as mariadb
# from django.http import HttpResponse
# Create your views here.

host = 'localhost'
user = 'root'
password = 'root'
database = 'test'


def home(request):
    return render(request, 'home/home.html')


def mod(request):
    return render(request, 'home/moderation.html')


def leveling(request):
    mariadb_connection = mariadb.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = mariadb_connection.cursor()

    cursor.execute("SELECT * FROM levels_table ORDER BY rank ASC")
    rows = cursor.fetchall()
    keys = ['user_id', 'msges_sent', 'exp', 'maxXp', 'level', 'username', 'rank', 'user_avatar_url']
    listOfDicts = []
    for i in rows:
        listOfDicts.append(convertToDict(keys, i))
    return render(request, 'home/leveling.html', {'dict': listOfDicts})


def currency(request):
    return render(request, 'home/currency.html')


def detail(request, user_id):
    mariadb_connection = mariadb.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = mariadb_connection.cursor()
    cursor.execute("SELECT * FROM levels_table WHERE user_id = '%s'" % user_id)
    rows = cursor.fetchall()
    keys = ['user_id', 'msges_sent', 'exp', 'maxXp', 'level', 'username', 'rank', 'user_avatar_url']
    listOfDicts = []
    for i in rows:
        listOfDicts.append(convertToDict(keys, i))
    return render(request, "home/detail.html", {'dict': listOfDicts})


def convertToDict(keys, values):
    return dict(zip(keys, values))
