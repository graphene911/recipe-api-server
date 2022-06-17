from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection

## API를 만들기 위한 class 작성
## class(클래스) = 변수와 함수로 구성된 묶음
## class는 상속이 가능하다.
## API를 만들기 위한 class는, flask_restful 라이브러리의
## Resource class를 상속해서 만들어야 한다.

class RecipeListResource(Resource) :
    # restful api의 method에 해당하는 함수 작성
    def post(self) :
        # api 실행 코드를 여기에 작성
        pass