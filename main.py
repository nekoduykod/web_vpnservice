import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates 
from fastapi_sqlalchemy import DBSessionMiddleware, db
from dotenv import load_dotenv
import os

from models import Users
from models import Users as ModelUsers
from models import Statistics
from models import Statistics as ModelStatistics

from schema import Users as SchemaUsers
from schema import Statistics as SchemaStatistics

load_dotenv(".env")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):     # I can use only def in these snippets
    return templates.TemplateResponse("home.html", {"request": request})

@app.get('/register', response_class=HTMLResponse)
async def registr_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
                                        
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, user: SchemaUsers):
    existing_user = db.session.query(Users).filter(Users.username == user.username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists"})
    db_user = ModelUsers(username=user.username, password=user.password, email=user.email)
    db.session.add(db_user)
    db.session.commit()
    return RedirectResponse(url="/login", status_code=303)

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, user: SchemaUsers):
    existing_user = db.session.query(Users).filter(Users.username == user.username, Users.password == user.password).first()
    if existing_user:
        return RedirectResponse(url="/account", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get('/account', response_class=HTMLResponse)
async def account_page(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})

@app.post('/account', response_class=HTMLResponse)
async def change_pass(request: Request, user: SchemaUsers):
    existing_user = db.session.query(Users).filter(Users.username == user.username, Users.password == user.password).first()
    if not existing_user:
        return templates.TemplateResponse("account.html", {"request": request, "error": "Incorrect current password"})
    if user.new_password != user.confirm_password:
        return templates.TemplateResponse("account.html", {"request": request, "error": "New password and confirm password do not match"})
    existing_user.password = user.new_password
    db.session.commit()   
    return RedirectResponse(url="/account", status_code=303)

# Next snippets are for http://127.0.0.1:8000/docs#/ 
@app.post("/add-user/", response_model=SchemaUsers)
def add_user(user: SchemaUsers):
    db_user = ModelUsers(username=user.username, password=user.password, email=user.email)
    db.session.add(db_user)
    db.session.commit()
    return db_user

@app.get("/users/")
def get_users():
    users = db.session.query(Users).all()
    return users

@app.post("/add-stat/", response_model=SchemaStatistics)
def add_statistic(stat: SchemaStatistics):
    db_statistics = ModelStatistics(id=stat.id, user_id=stat.user_id, page_transitions=stat.page_transitions, 
                                    vpn_site_transitions=stat.vpn_site_transitions, data_sent=stat.data_sent, 
                                    data_received=stat.data_received)
    db.session.add(db_statistics)
    db.session.commit()
    return db_statistics

@app.get("/stats/")
def get_stat():
    stats = db.session.query(Statistics).all()
    return stats

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)