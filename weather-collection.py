import contextlib
import json 
import logging
import os

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session as SASession
from typing import Dict
from typing import Optional
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus
from model import WeatherInfo, WeatherMeataInfo

SQL_ALCHEMY_CONN = "postgresql://test:test@localhost:5433/test"
Session: Optional[SASession] = None


def configure_orm(disable_connection_pool=False):
    logging.debug("Setting up DB connection pool (PID %s)" % os.getpid())
    global engine
    global Session

    engine = create_engine(SQL_ALCHEMY_CONN,
                           pool_size=0,
                           max_overflow=10,
                           pool_recycle=300,
                           pool_pre_ping=True,
                           pool_use_lifo=True)
    Session = scoped_session(
        sessionmaker(
            autocommit=False, autoflush=False, bind=engine, expire_on_commit=False,
        )
    )


def dispose_orm():
    """ Properly close pooled database connections """
    logging.debug("Disposing DB connection pool (PID %s)", os.getpid())
    global engine
    global Session

    if Session:
        Session.remove()
        Session = None
    if engine:
        engine.dispose()
        engine = None


def openapi_requests(url=None, parameter='?', **kwagrs) -> Dict[str, dict]:
    """공공 API 요청 폼

    Args:
        url ([type], optional): url. Defaults to None.
        parameter (str, optional): 명세 파라미터. Defaults to '?'.

    Returns:
        Dict[str, dict]: 요청 결과
    """    
    temp_dict = {}
    for i in kwagrs:
        temp_dict[quote_plus(i)] = kwagrs[i]

    queryParams = parameter + urlencode(temp_dict)
    request = Request(url + queryParams)
    request.get_method = lambda: 'GET'    

    try:
        response_body = urlopen(request).read().decode('utf-8')
    except Exception as e:
        return e

    return response_body


@contextlib.contextmanager
def create_session() -> scoped_session:
    """Contextmanager that will create and teardown a session.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def asos_request(self, dataCd: str = 'ASOS',
                 dateCd: str = 'DAY', 
                 startDt: int = None,
                 endDt: int = None, 
                 stnIds: int = None) -> bool:
        """ ASOS 종관 데이터 요청 및 등록

        Args:
            dataCd (str, optional): 데이터 코드. Defaults to 'ASOS'.
            dateCd (str, optional): 데이트 코드. Defaults to 'DAY'.
            startDt (int, optional): 시작 날짜. Defaults to None.
            endDt (int, optional): 종료 날짜. Defaults to None.
            stnIds (int, optional): 지점 번호. Defaults to None.

        Returns:
            bool: 성공/실패self.__dict__,
        """
        try:
            values = openapi_requests(
                url=self.url, 
                ServiceKey=self.decodingKey,
                dataType=self.dataType,
                numOfRows=self.numOfRows,
                pageNo=self.pageNo,
                dataCd=dataCd,
                dateCd=dateCd,
                startDt=startDt,
                endDt=endDt,
                stnIds=stnIds
            )
            values = json.loads(values)
        except Exception:
            return False
        try:
            values = values['response']['body']['items']['item']
        except Exception as e:
            print(f'Location {stnIds}No Response {e}')
            return False

        with create_session() as session:
            emd_cd = session.query(WeatherMeataInfo).\
                filter(WeatherMeataInfo.loc_id == stnIds).first()
            key_data = session.query(WeatherInfo.id).\
                filter(WeatherInfo.emd_cd == emd_cd.emd_cd).all()
            result_list = []
            for index, value in enumerate(values):
                # TODO 시각적 잡음 왈러스 연산 + 반복 코드 수정 
                # 도커에서 파이썬 3.6으로 빌드되어있어 왈러스연산 사용 불가
                # 변경시 GDAL 버전 변경해야 함
                ids = "WT" + str(value['tm']).replace("-", "") + str(int(stnIds)).zfill(3)
                if tuple([ids]) in key_data:
                    continue
                try:
                    result = {
                        'updated_at': datetime.now(),
                        'id': ids, 
                        'acq_dt': datetime.strptime(value['tm'], '%Y-%m-%d'),
                        'emd_cd': emd_cd.emd_cd,
                        'avgts': value['avgTs'] if value['avgTs'] else None,
                        'avgpa': value['avgPa'] if value['avgPa'] else None,
                        'max_temp': value['maxTa'] if value['maxTa'] else None,
                        'min_temp': value['minTa'] if value['minTa'] else None,
                        'ss_amount': value['sumSsHr'] if value['sumSsHr'] else None,
                        'rn_amount': value['sumRn'] if value['sumRn'] else None,
                        'hd': value['avgRhm'] if value['avgRhm'] else None,
                        'is_amount': value['sumGsr'] if value['sumGsr'] else None,
                        'cc_amount': value['avgTca'] if value['avgTca'] else None,
                        'max_wind': value['maxWs'] if value['maxWs'] else None,
                        'min_wind': None,
                        'snowd': value['ddMes'] if value['ddMes'] else None
                    }
                    result_list.append(WeatherInfo(**result))

                except Exception as e:
                    print(f"No data Value error {e}")
            session.bulk_save_objects(result_list, return_defaults=True)

        return True
