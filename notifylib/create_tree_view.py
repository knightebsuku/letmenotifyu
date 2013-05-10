#!/usr/bin/python


def create_parent(cursor,series_column):
    x=1
    cursor.execute("SELECT title,number_of_seasons from series")
    for results in cursor.fetchall():
        parent_title=series_column.append(None,[results[0]])
        while x<=int(results[1]):
            create_seasons(cursor,results[0],parent_title,series_column,x)
            x+=1
        x=1


def create_seasons(cursor,series_title,parent_title,series_column,x):
    name="season "+str(x)
    sql_name="%season-"+str(x)+"%"
    series_number=series_column.append(parent_title,[name])
    cursor.execute("SELECT episode_name FROM episodes WHERE title=? and episode_link LIKE ?",(series_title,sql_name))
    for episode in cursor.fetchall():
        episodes=series_column.append(series_number,[episode[0]])
    

        
        
