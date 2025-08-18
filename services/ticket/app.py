from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import database, models

# Create tables in the database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Ticket Service")

@app.get("/tickets")
def get_tickets(db: Session = Depends(database.get_db)):
    # TODO: Implement actual ticket retrieval logic
    return {"message": "Get tickets endpoint (MySQL connected)"}

# TODO: Add endpoints for creating, updating, and getting a single ticket