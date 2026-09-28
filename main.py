from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

#model creation
class Test(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    
    
# connecting with database .db file
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
    
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/testdata/")
def create_testdata(test: Test, session: SessionDep) -> Test:
    session.add(test)
    session.commit()
    session.refresh(test)
    return test

@app.get("/testdata/")
def read_testdata(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Test]:
    testdata = session.exec(select(Test).offset(offset).limit(limit)).all()
    return testdata

@app.get("/testdata/{test_id}")
def read_testdata(test_id: int, session: SessionDep) -> Test:
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="test data not found")
    return test

@app.delete("/testdata/{test_id}")
def delete_testdata(test_id: int, session: SessionDep):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="testdata not found")
    session.delete(test)
    session.commit()
    return {"ok": True}

@app.put("/testdata/{test_id}")
def update_testdata(test_id: int, test_update: Test, session: SessionDep) -> Test:
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="test data not found")
    
    test_data = test_update.model_dump(exclude_unset=True)
    for key, value in test_data.items():
        setattr(test, key, value)
            
    session.add(test)
    session.commit()
    session.refresh(test)
    return test