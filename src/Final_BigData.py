#_*_coding:utf-8 _*_
'''
Created on 2019. 11. 18.

@author: 강아연
'''

import urllib.request as urls
import json
import calendar
import pymysql
import matplotlib.pyplot as plt
import matplotlib
import sys
import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats, polyval
from matplotlib import font_manager

################### 유동 IP이므로 WIFI가 바뀌면 IP주소를 바꿔주기 ######################
############### 서비스키 일 3000회 제한있으므로 오류나면 서비스키 다른걸로 바꿔주기 #################
def font_Function():
    font_location="C:/Windows/Fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_location).get_name()
    matplotlib.rc('font', family=font_name)
    matplotlib.rcParams['axes.unicode_minus'] = False
    
def insert1BoxOffice(): #처음 실행시 필요해서 만들어 놓음 1분기데이터
    try:
        for i in range(1,4,1): # 1분기 데이터 (1,2,3) 월
            for j in range(1,calendar.monthrange(2019, i)[1],7): #일 , 2019년도의 i월의 마지막 일자를 구한다.
                if(len(str(j))==1):
                    date="0"+str(i)+"0"+str(j) #한자리 숫자일 경우 앞에 0을 붙여줘야함
                else:
                    date="0"+str(i)+str(j)
                url='http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json?'
                key='key=a41a4659ac1a92e4e78fdab1cb227521'
                targetDt=f'&targetDt=2019{date}'
                weekGb='&weekGb=0'
                lst=[]
                showR=[]
                request=urls.Request(url+key+targetDt+weekGb)
                response=urls.urlopen(request) # 해당 url의 데이터를 오픈
                rescode = response.getcode() # 응답 상태 코드를 가져올 수 있음
                json_data = json.loads(response.read())
                
                for movie in json_data['boxOfficeResult']['weeklyBoxOfficeList']:
                    lst.append(movie)
                for movie in json_data['boxOfficeResult']['showRange']: #어떤 주간의 것인지
                    showR.append(movie)
                for boxOffice,showRa in zip(lst,showR):
                    #print(''.join(showR)) #리스트의 쪼개진 것들을 문자열로 하나로 묶어주기
                    #print(boxOffice['rank'],u'영화제목:',boxOffice['movieNm'],u'개봉일:',boxOffice['openDt'],u'해당일의 관객수 :',boxOffice['audiCnt'],boxOffice['audiAcc'])
                    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
                    curs = conn.cursor()
                    sql = f"select * from quarter1 where movieNm=\'{boxOffice['movieNm']}\'"
                    curs.execute(sql)
                    result = curs.fetchall() 
                    if(curs.execute(sql)==1):  # 이미 영화가 있다면 관객 수를 +해서 업데이트 해주고 누적 관객수는 아예 다시 새로 업데이트 해줌
                        if(result[0][4]==''.join(showR)): # 월의 마지막 일과 월 초의 일의 경우 주간 리스트가 겹쳐서 두번 도는 경우가 있기 때문에 처리해줌
                            j=j+7
                            break
                        #print(''.join(showR))
                        sql1 = 'update quarter1 set audiCnt=audiCnt+\'%s\',audiAcc=\'%s\' where movieNm=\'%s\''%(boxOffice['audiCnt'],boxOffice['audiAcc'],boxOffice['movieNm'])
                        sql12 = 'update quarter1 set salesAmt=salesAmt+\'%s\',scrnCnt=scrnCnt+\'%s\' where movieNm=\'%s\''%(boxOffice['salesAmt'],boxOffice['scrnCnt'],boxOffice['movieNm'])
                        sql13='update quarter1 set showRange=\'%s\' where movieNm=\'%s\''%(''.join(showR),boxOffice['movieNm'])
                        curs.execute(sql1)
                        curs.execute(sql12)
                        curs.execute(sql13)
                        sql2='select movieNm,audiCnt from quarter1 where movieNm=\'%s\''%(boxOffice['movieNm'])
                        curs.execute(sql2)
                        result = curs.fetchall()  
                        #print(result[0][0],result[0][1])
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('update') #확인 용
                    else: # 영화 이름이 없는 거라면 
                        sql = 'insert into quarter1(movieNm,openDt,audiCnt,audiAcc,showRange,salesAmt,scrnCnt,movieCd) values (\'%s\',\'%s\',%d,%d,\'%s\',%d,%d,%d)'%(boxOffice['movieNm'],boxOffice['openDt'],int(boxOffice['audiCnt']),int(boxOffice['audiAcc']),''.join(showR),int(boxOffice['salesAmt']),int(boxOffice['scrnCnt']),int(boxOffice['movieCd']))
                        curs.execute(sql)
                        #print(''.join(showR))
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('insert') #확인 용
                    conn.commit()
        conn.close()
        if(rescode==200):
            response_body = response.read()
        else:
            print("에러 :" + rescode)
    except Exception as err123:
        print(err123)
    else:
        print('완료 되었습니다 !')    

def genreChart(): #1분기 장르 차트 
    font_Function() 
    lst=[]
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
    curs = conn.cursor()
    
    sql = 'select movieCd from quarter1'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(len(result)):
        url='http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?'
        key='key=6e86cb8b695c10ad5c5238ebbfc71df6'
        movieCd2=f'&movieCd={result[i][0]}'
        request=urls.Request(url+key+movieCd2)
        response=urls.urlopen(request) # 해당 url의 데이터를 오픈
        json_data = json.loads(response.read())
        for movie in json_data['movieInfoResult']['movieInfo']['genres']:
            lst.append(movie['genreNm'])
    df=pd.DataFrame(lst,columns=['장르'])
    genre_group = df.groupby(['장르'])
    df2=pd.DataFrame(genre_group.size(),columns=['개수'])
    #index_v=df2.index.values
    #values_v=df2.values.tolist()
    #v_L=[]
    #for i in range(len(values_v)):
    #    v_L.append(values_v[i][0])
    #plt.bar(np.arange(len(index_v)),values_v)
    #plt.show()
    return df2.T

def insert2BoxOffice(): #처음 실행시 필요해서 만들어 놓음 2분기데이터
    try:
        for i in range(4,7,1): # 2분기 데이터 (4,5,6)
            for j in range(1,calendar.monthrange(2019, i)[1],7): #2019년도의 i월의 마지막 일자를 구한다.
                if(len(str(j))==1):
                    date="0"+str(i)+"0"+str(j) #한자리 숫자일 경우 앞에 0을 붙여줘야함
                else:
                    date="0"+str(i)+str(j)
                url='http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json?'
                key='key=a41a4659ac1a92e4e78fdab1cb227521'
                targetDt=f'&targetDt=2019{date}'
                weekGb='&weekGb=0'
                lst=[]
                showR=[]
                request=urls.Request(url+key+targetDt+weekGb)
                response=urls.urlopen(request) # 해당 url의 데이터를 오픈
                rescode = response.getcode() # 응답 상태 코드를 가져올 수 있음
                json_data = json.loads(response.read())
                
                for movie in json_data['boxOfficeResult']['weeklyBoxOfficeList']:
                    lst.append(movie)
                for movie in json_data['boxOfficeResult']['showRange']: #어떤 주간의 것인지
                    showR.append(movie)
                for boxOffice,showRa in zip(lst,showR):
                    #print(''.join(showR)) #리스트의 쪼개진 것들을 문자열로 하나로 묶어주기
                    #print(boxOffice['rank'],u'영화제목:',boxOffice['movieNm'],u'개봉일:',boxOffice['openDt'],u'해당일의 관객수 :',boxOffice['audiCnt'],boxOffice['audiAcc'])
                    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
                    curs = conn.cursor()
                    sql = f"select * from quarter2 where movieNm=\'{boxOffice['movieNm']}\'"
                    curs.execute(sql)
                    result = curs.fetchall() 
                    if(curs.execute(sql)==1):  # 이미 영화가 있다면 관객 수를 +해서 업데이트 해주고 누적 관객수는 아예 다시 새로 업데이트 해줌
                        #print('리절트랑 조인이랑 같은지 : ',result[0][4],''.join(showR))
                        if(result[0][4]==''.join(showR)): # 월의 마지막 일과 월 초의 일의 경우 주간 리스트가 겹쳐서 두번 도는 경우가 있기 때문에 처리해줌
                            j=j+7
                            break
                        #print(''.join(showR))
                        sql1 = 'update quarter2 set audiCnt=audiCnt+\'%s\',audiAcc=\'%s\' where movieNm=\'%s\''%(boxOffice['audiCnt'],boxOffice['audiAcc'],boxOffice['movieNm'])
                        sql12 = 'update quarter2 set salesAmt=salesAmt+\'%s\',scrnCnt=scrnCnt+\'%s\' where movieNm=\'%s\''%(boxOffice['salesAmt'],boxOffice['scrnCnt'],boxOffice['movieNm'])
                        sql13='update quarter2 set showRange=\'%s\' where movieNm=\'%s\''%(''.join(showR),boxOffice['movieNm'])
                        curs.execute(sql1)
                        curs.execute(sql12)
                        curs.execute(sql13)
                        sql2='select movieNm,audiCnt from quarter2 where movieNm=\'%s\''%(boxOffice['movieNm'])
                        curs.execute(sql2)
                        result = curs.fetchall()  
                        #print(result[0][0],result[0][1])
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('update') #확인 용
                    else: # 영화 이름이 없는 거라면 
                        sql = 'insert into quarter2(movieNm,openDt,audiCnt,audiAcc,showRange,salesAmt,scrnCnt,movieCd) values (\'%s\',\'%s\',%d,%d,\'%s\',%d,%d,%d)'%(boxOffice['movieNm'],boxOffice['openDt'],int(boxOffice['audiCnt']),int(boxOffice['audiAcc']),''.join(showR),int(boxOffice['salesAmt']),int(boxOffice['scrnCnt']),int(boxOffice['movieCd']))
                        curs.execute(sql)
                        #print(''.join(showR))
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('insert') #확인 용
                    conn.commit()
        conn.close()
        if(rescode==200):
            response_body = response.read()
        else:
            print("에러 :" + rescode)
    except Exception as err123:
        print(err123)
    else:
        print('완료 되었습니다 !')

def genre2Chart(): #2분기 장르 차트
    font_Function()
    lst=[]
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
    curs = conn.cursor()
    sql = 'select movieCd from quarter2'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(len(result)):
        url='http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?'
        key='key=6e86cb8b695c10ad5c5238ebbfc71df6'
        movieCd2=f'&movieCd={result[i][0]}'
        request=urls.Request(url+key+movieCd2)
        response=urls.urlopen(request) # 해당 url의 데이터를 오픈
        json_data = json.loads(response.read())
        for movie in json_data['movieInfoResult']['movieInfo']['genres']:
            lst.append(movie['genreNm'])
    df=pd.DataFrame(lst,columns=['장르'])
    genre_group = df.groupby(['장르'])
    df2=pd.DataFrame(genre_group.size(),columns=['개수'])
    #index_v=df2.index.values
    #values_v=df2.values.tolist()
    #v_L=[]
    #for i in range(len(values_v)):
    #    v_L.append(values_v[i][0])
    return df2.T
            
def insert3BoxOffice(): #처음 실행시 필요해서 만들어 놓음 3분기 데이터
    try:
        for i in range(7,10,1): # 3분기 데이터 (7,8,9)
            for j in range(1,calendar.monthrange(2019, i)[1],7): #2019년도의 i월의 마지막 일자를 구한다.
                if(len(str(j))==1):
                    date="0"+str(i)+"0"+str(j) #한자리 숫자일 경우 앞에 0을 붙여줘야함
                else:
                    date="0"+str(i)+str(j)
                url='http://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json?'
                key='key=a41a4659ac1a92e4e78fdab1cb227521'
                targetDt=f'&targetDt=2019{date}'
                weekGb='&weekGb=0'
                lst=[]
                showR=[]
                request=urls.Request(url+key+targetDt+weekGb)
                response=urls.urlopen(request) # 해당 url의 데이터를 오픈
                rescode = response.getcode() # 응답 상태 코드를 가져올 수 있음
                json_data = json.loads(response.read())
                
                for movie in json_data['boxOfficeResult']['weeklyBoxOfficeList']:
                    lst.append(movie)
                for movie in json_data['boxOfficeResult']['showRange']: #어떤 주간의 것인지
                    showR.append(movie)
                for boxOffice,showRa in zip(lst,showR):
                    #print(''.join(showR)) #리스트의 쪼개진 것들을 문자열로 하나로 묶어주기
                    #print(boxOffice['rank'],u'영화제목:',boxOffice['movieNm'],u'개봉일:',boxOffice['openDt'],u'해당일의 관객수 :',boxOffice['audiCnt'],boxOffice['audiAcc'])
                    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
                    curs = conn.cursor()
                    sql = f"select * from quarter3 where movieNm=\'{boxOffice['movieNm']}\'"
                    curs.execute(sql)
                    result = curs.fetchall() 
                    if(curs.execute(sql)==1):  # 이미 영화가 있다면 관객 수를 +해서 업데이트 해주고 누적 관객수는 아예 다시 새로 업데이트 해줌
                        #print('리절트랑 조인이랑 같은지 : ',result[0][4],''.join(showR))
                        if(result[0][4]==''.join(showR)): # 월의 마지막 일과 월 초의 일의 경우 주간 리스트가 겹쳐서 두번 도는 경우가 있기 때문에 처리해줌
                            j=j+7
                            break
                        #print(''.join(showR))
                        sql1 = 'update quarter3 set audiCnt=audiCnt+\'%s\',audiAcc=\'%s\' where movieNm=\'%s\''%(boxOffice['audiCnt'],boxOffice['audiAcc'],boxOffice['movieNm'])
                        sql12 = 'update quarter3 set salesAmt=salesAmt+\'%s\',scrnCnt=scrnCnt+\'%s\' where movieNm=\'%s\''%(boxOffice['salesAmt'],boxOffice['scrnCnt'],boxOffice['movieNm'])
                        sql13='update quarter3 set showRange=\'%s\' where movieNm=\'%s\''%(''.join(showR),boxOffice['movieNm'])
                        curs.execute(sql1)
                        curs.execute(sql12)
                        curs.execute(sql13)
                        sql2='select movieNm,audiCnt from quarter3 where movieNm=\'%s\''%(boxOffice['movieNm'])
                        curs.execute(sql2)
                        result = curs.fetchall()  
                        #print(result[0][0],result[0][1])
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('update') #확인 용
                    else: # 영화 이름이 없는 거라면 
                        sql = 'insert into quarter3(movieNm,openDt,audiCnt,audiAcc,showRange,salesAmt,scrnCnt,movieCd) values (\'%s\',\'%s\',%d,%d,\'%s\',%d,%d,%d)'%(boxOffice['movieNm'],boxOffice['openDt'],int(boxOffice['audiCnt']),int(boxOffice['audiAcc']),''.join(showR),int(boxOffice['salesAmt']),int(boxOffice['scrnCnt']),int(boxOffice['movieCd']))
                        curs.execute(sql)
                        #print(''.join(showR))
                        #print(boxOffice['movieNm'],boxOffice['audiCnt'])
                        #print('insert') #확인 용
                    conn.commit()
        conn.close()
        if(rescode==200):
            response_body = response.read()
        else:
            print("에러 :" + rescode)
    except Exception as err123:
        print(err123)
    else:
        print('완료 되었습니다 !')

def genre3Chart(): #3분기 장르 차트 
    font_Function()
    lst=[]
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8',autocommit=True)    
    curs = conn.cursor()
    sql = 'select movieCd from quarter3'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(len(result)):
        url='http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?'
        key='key=6e86cb8b695c10ad5c5238ebbfc71df6'
        movieCd2=f'&movieCd={result[i][0]}'
        request=urls.Request(url+key+movieCd2)
        response=urls.urlopen(request) # 해당 url의 데이터를 오픈
        json_data = json.loads(response.read())
        for movie in json_data['movieInfoResult']['movieInfo']['genres']:
            lst.append(movie['genreNm'])
    df=pd.DataFrame(lst,columns=['장르'])
    genre_group = df.groupby(['장르'])
    df2=pd.DataFrame(genre_group.size(),columns=['개수'])
    #index_v=df2.index.values
    #values_v=df2.values.tolist()
    #v_L=[]
    #for i in range(len(values_v)):
    #    v_L.append(values_v[i][0])
    return df2.T

def genreTotalChart(): #모든 장르 데이터 리턴 받아서 여기서 처리한다.
    df1= genreChart()
    df2=genre2Chart()
    df3=genre3Chart()
    colors=['red','gold','olive','mediumblue','green','orchid','lightpink','tomato','magenta','slategray','cyan','y','saddlebrown','slateblue','cornflowerblue','yellow','wheat','peru','turquoise','palegreen','cadetblue']
    result=pd.DataFrame()
    result=result.merge(df1,right_index=True,left_index=True,how='outer')
    result=result.merge(df2,how='outer')
    result=result.merge(df3,how='outer')
    result.rename(index={0:'1분기',1:'2분기',2:'3분기'},inplace=True)
    print(result)
    ax = result.plot(kind='bar',title="분기별 장르별 개봉 수",width=0.5,color=colors)
    for p in ax.patches: #ax.patches란 ax가 가르키는 그래프에서, 막대들을 담고있는 리스트다.
        ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005 ))
        
    plt.show()
    
    
def quarterChart(): #1~3분기 1~10위 
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8')
    curs = conn.cursor()
    for i in range(1,4,1):
        sql=f'select movieNm,openDt,audiCnt from quarter{i} order by audiCnt desc limit 10;'
        curs.execute(sql)
        result=curs.fetchall()
        result=np.array(result)
        exec("df%d = pd.DataFrame(result,columns=['영화이름','개봉일','%d분기 관객수'],index=np.arange(1,11,1))" % (i,i))
        for k in range(10):
            exec("df%d.iloc[%d,2]=format(int(df%d.iloc[%d,2]),',')"%(i,k,i,k)) #숫자 세자리마다 쉼표 찍어주려고
            
    for j in range(1,4,1):
        print(f'{j}분기 관객 수 기준 1~10위')
        exec('print(df%d)'%j)
    conn.commit()
    conn.close()
    
def seeChart(): # 시각화 차트 매출액과 스크린수의 상관관계 
    font_Function() 
    salesAmt=[]
    scrnCnt=[]
    salesAmt2=[]
    scrnCnt2=[]
    salesAmt3=[]
    scrnCnt3=[]
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8')
    curs = conn.cursor()
    sql=f'select salesAmt,scrnCnt from quarter1 order by audiCnt desc limit 30;'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(30):
        salesAmt.append(result[i][0])
        scrnCnt.append(result[i][1])
    df1=pd.DataFrame(salesAmt,columns=['매출액'])
    df2=pd.DataFrame(scrnCnt, columns=['스크린수'])
    result1=pd.DataFrame()
    result1=result1.merge(df1,right_index=True,left_index=True,how='outer')
    result1=result1.merge(df2,right_index=True,left_index=True,how='outer')
    result1['분기']='1분기'
    
    sql=f'select salesAmt,scrnCnt from quarter2 order by audiCnt desc limit 30;'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(30):
        salesAmt2.append(result[i][0])
        scrnCnt2.append(result[i][1])
    df3=pd.DataFrame(salesAmt2,columns=['매출액'])
    df4=pd.DataFrame(scrnCnt2, columns=['스크린수'])
    result2=pd.DataFrame()
    result2=result2.merge(df3,right_index=True,left_index=True,how='outer')
    result2=result2.merge(df4,right_index=True,left_index=True,how='outer')
    result2['분기']='2분기'
    
    sql=f'select salesAmt,scrnCnt from quarter3 order by audiCnt desc limit 30;'
    curs.execute(sql)
    result = curs.fetchall() 
    for i in range(30):
        salesAmt3.append(result[i][0])
        scrnCnt3.append(result[i][1])
    df5=pd.DataFrame(salesAmt3,columns=['매출액'])
    df6=pd.DataFrame(scrnCnt3, columns=['스크린수'])
    result3=pd.DataFrame()
    result3=result3.merge(df5,right_index=True,left_index=True,how='outer')
    result3=result3.merge(df6,right_index=True,left_index=True,how='outer')
    result3['분기']='3분기'
    
    result1=result1.merge(result2,how='outer')
    result1=result1.merge(result3,how='outer')
    
    sns.relplot(x="매출액", y="스크린수", hue="분기", size="스크린수", sizes=(40, 400), alpha=.5, palette="muted", height=6, data=result1)
    sns.lmplot(x="매출액", y="스크린수", col="분기", hue="분기", data=result1, palette="muted", height=4, scatter_kws={"s": 10})
    #위에것 안될시에 밑에거 왜냐 seaborn 버전이 달라서 ㅠㅠ
    #sns.lmplot(x="매출액", y="스크린수", col="분기", hue="분기", data=result1, palette="muted", size=4, scatter_kws={"s": 10})

    plt.show()
    conn.close()

def totalChart(): #1,2,3분기 통합해서 관객 수 기준으로 순위 구하기
    conn = pymysql.connect(host='172.30.1.53', user='root', password='dlsgkvmfwpr@_',db='bigdata',charset='utf8')
    curs = conn.cursor()
    
    sql1=u'select movieNm,openDt,audiCnt from quarter1;'
    sql2=u'select movieNm,openDt,audiCnt from quarter2;'
    sql3=u'select movieNm,openDt,audiCnt from quarter3;'
    curs.execute(sql1)
    result1 = curs.fetchall()
    result1 = np.array(result1)
    df1=pd.DataFrame(result1)
    curs.execute(sql2)
    result2 = curs.fetchall()
    result2 = np.array(result2)
    df2=pd.DataFrame(result2)
    curs.execute(sql3)
    result3 = curs.fetchall()
    result3 = np.array(result3)
    df3=pd.DataFrame(result3)
      
    conn.commit()
    conn.close()
    
    result=pd.DataFrame()
    result=result.merge(df1,right_index=True,left_index=True,how='outer')
    result=result.merge(df2,how='outer')
    result=result.merge(df3,how='outer')
    result[2]=result[2].astype(int)
    result=result.rename(columns={0:'영화이름',1:'개봉일',2:'관객수'})

    
    df=result.sort_values(by=['관객수'], axis=0,ascending=False).head(10)
    df.reset_index(drop=True,inplace=True)
    df.index=[1,2,3,4,5,6,7,8,9,10]
    print('※ 1/2/3분기 통합 순위')
    for i in range(10):
        df.iloc[i,2]=format(int(df.iloc[i,2]),',') #숫자 세자리마다 쉼표 찍어주려고
    print(df)
    

while(True):
    print('원하는 번호를 입력해주세요 ')
    print('1)1~3분기 관객 수 1~10위 2)1~3분기 통합 관객 수 1~10위 3)분기별 매출액과 스크린 수 상관관계 시각화 4)분기별 영화 장르개봉수 시각화  5)종료')
    number=int(input())
    if(number==1):
        quarterChart()
    elif(number==2):
        totalChart()
    elif(number==3):
        seeChart()
    elif(number==4): # 불러오는데 오래걸림
        genreTotalChart()
    elif(number==5):
        print('종료되었습니다.')
        sys.exit(0)
        break