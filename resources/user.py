from http import HTTPStatus
from flask import request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector
from email_validator import validate_email, EmailNotValidError

from utils import check_password, hash_password


# 회원가입은 Method = POST, '/users/register', data = nickname, email, password
class UserRegisterResource(Resource) :
    def post(self) :
        
        # {
        #     "username": "홍길동",
        #     "email": "abc@gmail.com",
        #     "password": "1234"
        # }
        
        # 1. 클라이언트가 body에 보내준 json을 받아온다.
        data = request.get_json()
        

        # 2. 이메일 주소형식이 제대로 된 주소형식인지 확인하는 코드작성.
        try:
            validate_email(data['email'])

        except EmailNotValidError as e:
            
            print(str(e))

            return {"error" : str(e)}, 400 


        # 3. 비밀번호의 길이가 유효한지 체크한다.
        # 비밀번호 길이는 4자리 이상, 12자리 이하로 한다. (예외처리)

        if len(data['password']) < 4 or len(data['password']) > 12 :
            return {"error" : '비밀번호의 길이를 확인하세요'}, 400



        # 4. 비밀번호를 암호화 한다.
        # data['password']

        hashed_password = hash_password(data['password'])

        print(hashed_password)
        

        # 5. DB에 회원정보를 저장한다.
        # 받아온 데이터를 DB에 저장하면 된다.
        try :
            # 데이터 insert 
            # 5-1. DB에 연결
            connection = get_connection()

            # 5-2. 쿼리문 만들기
            query = '''insert into user
                    (username, email, password)
                    values
                    ( %s , %s , %s );'''
            
            record = (data['username'], data['email'], hashed_password )

            # 5-3. 커서를 가져온다.
            cursor = connection.cursor()

            # 5-4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5-5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
            connection.commit()

            # 5-5-1 DB에 저장된 아이디값 가져오기
            user_id = cursor.lastrowid
            # 5-6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503
        
        # user_id를 바로 보내면 안되고
        # JWT로 암호화 해서 보내준다.
        
        access_token = create_access_token(user_id)
        # 토큰 유효기간 만료 시키는 방법
        # access_token = create_access_token(user_id, expires_delta=datetime.timedelta(minutes = 1))

        return {"result" : "success", 'access_token' : access_token}, 200
        
# 로그인하는 API
class UserLoginResource(Resource) :
    def post(self) :
        # {
        #     "email": "abc@gmail",
        #     "password": "1234"
        # }

        # 1. 클라이언트가 body에 보내준 json을 받아온다.
        data = request.get_json()
        
        # 2. 이메일로 DB에 이 이메일과 일치하는 데이터를 가져온다.
        try :
            connection = get_connection()

            query = '''select *
                    from user
                    where email = %s;'''

            record = (data['email'],)

            # select 문은, dictionary = True 를 해준다.
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            print(result_list)

            # 중요! 디비에서 가져온 timestamp 는 
            # 파이썬의 datetime 으로 자동 변경된다.
            # 문제는! 이데이터를 json 으로 바로 보낼수 없으므로,
            # 문자열로 바꿔서 다시 저장해서 보낸다.
            i = 0
            for record in result_list :
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
                i = i + 1                

            cursor.close()
            connection.close()

            print(result_list)

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503

        # 3. 행이 result_list 행의 갯수가 1개이면
        #    user 데이터를 정상적으로 받아온 것이고
        #    행의 갯수가 0이면, 요청한 이메일은
        #    회원가입이 되어있지 않은 이메일이다.

        if len(result_list) != 1 :
            return {'error' : '회원가입인 안된 이메일입니다.'}, 400 

        # 4. 비밀번호가 맞는지 확인한다.
        user_info = result_list[0]

        # data['password'] 와 user_info['password']를 비교
        check = check_password(data['password'], user_info['password'])

        if check == False :
            return {'error' : '비밀번호가 맞지 않습니다..'}, 400 
        
        access_token = create_access_token(user_info['id'])
        # 토큰 유효기간 만료 시키는 방법
        # access_token = create_access_token(user_info['id'], expires_delta=datetime.timedelta(minutes = 1))

        return {'result' : 'success', 'access_token' : access_token}, 200


jwt_blacklist = set()

# 로그아웃 기능을 하는 클래스
class UserLogoutResource(Resource) :
    @jwt_required()
    def post(self) :
        
        jti = get_jwt()['jti']
        print(jti)

        jwt_blacklist.add(jti)
        
        return {'result' : 'success'}, 200