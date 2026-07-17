from sqlalchemy import select, union_all, Column, Integer
from sqlalchemy.orm import declarative_base, aliased, Session
Base=declarative_base()
class M(Base):
    __tablename__='m'
    id=Column(Integer, primary_key=True)
s = Session()
q1 = s.query(M).limit(10)
q2 = s.query(M).limit(10)
u = union_all(q1.statement, q2.statement)
aliased_m = aliased(M, u.subquery())
print(aliased_m)
