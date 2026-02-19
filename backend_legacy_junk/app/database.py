from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./realestate.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PropertyListing(Base):
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True, index=True)
    sqft = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    price = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
