from sqlalchemy import Column
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime, Float, String
from sqlalchemy.ext.declarative import declarative_base


class TimestampMixin(object):
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성일자
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )  # 수정일자


Base = declarative_base()


class WeatherInfo(Base, TimestampMixin):
    """기상_정보_외부"""

    __tablename__ = "weather_info"

    id = Column(String, primary_key=True)  # 아이디 (:WT00000000)
    acq_dt = Column(DateTime)  # 취득_일자
    emd_cd = Column(String)  # 읍면동_코드
    max_temp = Column(Float)  # 최고_기온
    min_temp = Column(Float)  # 최저_기온
    ss_amount = Column(Float)  # 일조량
    rn_amount = Column(Float)  # 강우량
    hd = Column(Float)  # 습도
    is_amount = Column(Float)  # 일사량
    cc_amount = Column(Float)  # 운량
    max_wind = Column(Float)  # 최대풍속
    min_wind = Column(Float)  # 최소풍속
    snowd = Column(Float)  # 적설량
    avgts = Column(Float)  # 평균 지면 기온
    avgpa = Column(Float)  # 평균 증기압


class WeatherMeataInfo(Base, TimestampMixin):
    """기상_관측소_메타_정보"""

    __tablename__ = 'weather_meata_info'

    loc_id = Column(Float, primary_key=True)  # 지점번호
    lon = Column(Float)  # 경도
    lat = Column(Float)  # 위도
    loc_cd = Column(Float)  # 지점 특성코드
    hight = Column(Float)  # 노장 해발고도
    loc_kor_nm = Column(String)  # 지점 국문 명
    loc_eng_nm = Column(String)  # 지점 영문 명
    emd_cd = Column(String)  # 읍면동 코드
    acq_dt = Column(String)  # 취득 일자
