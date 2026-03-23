from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# Create base class for models
Base = declarative_base()
metadata = MetaData()