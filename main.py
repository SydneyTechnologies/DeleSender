from fastapi import FastAPI, HTTPException, status, Depends
from utils import *
from models import CreateOrderModel, Order, UpdateOrderStatusModel, OrderState
from pydantic import BaseModel, ValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import pymongo
import certifi
from uuid import UUID

mongo_db_url = config("MONGO_DB_URL")
db_client = pymongo.MongoClient(mongo_db_url, tlsCAFile = certifi.where(), uuidRepresentation="standard")

app = FastAPI()
authentication_scheme = OAuth2PasswordBearer(tokenUrl="login")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://example.com",
    "https://www.example.com",
]

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# models
class User(BaseModel):
    email: str
    full_name: str
    password: str
    phone_number: str

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "email": "person@email.com",
            "full_name": "John Doe", 
            "password": "XXXXXXXX",
            "phone_number": "+2348073390336"
        }
    

class TokenPayload(BaseModel):
    exp: int
    sub: str
    

@app.post("/register", summary="Create new end users for the sender application")
def register(user: User):
    # first we need to check if the user exists in our database 
    email = user.email
    if email is not None:
        email = db_client.sender.User.find_one({"email": email})
        if email is not None:
            # meaning the email exists then we want to raise an error and tell the user that a user already exists with this email
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
        
        # if the email does not exist then we create a new user 
        # but before that we must hash the users password
        password = user.password
        # hashed password
        hashed_password = get_hashed_password(password=password)
        # now we swap the actual string password with the hashed variant
        user.password = hashed_password
        # now insert this new user into the database 
        # dob = user_data.date_of_birth
        # user_data.date_of_birth = str(dob)
        new_user = db_client.sender.User.insert_one(user.dict())

        inserted_user = db_client.sender.User.find_one({"_id": new_user.inserted_id})

        # convert the user document to a User object and return it
        inserted_user.pop("_id", None)
        return User(**inserted_user)


@app.post("/login", summary="Login User")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db_client.sender.User.find_one({"email": form_data.username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    # so the user exists in the db now we have to validate if the password is correct 
    entered_string_password = form_data.password
    hashed_user_password = User(**user).password

    if not verify_password(entered_string_password, hashed_user_password):
        # if the password does not match then raise an exception 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    # however if the data does exist and the passwords are the same then we return the access and refresh tokens 

    return {
        "access_token": create_access_token(user["email"]),
        "refresh_token": create_refresh_token(user["email"]),
    }


def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT"))) -> User:
    # now we have the token we need to decode it
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


    user = db_client.sender.User.find_one({"email": token_data.sub})
    user.pop("_id")
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    return User(**user)

@app.post("/orders", summary="This endpoint that creates orders associated with a user")
def createOrder(order: CreateOrderModel, user: User = Depends(get_current_user)):
    order_collection = db_client.sender.order 
    # we take the order model and update the actual order 
    # first we check if the user creating the request is actually this user 
    if order.owner_email == user.email:
        # if the are the same users then proceed to creating the order 
        new_order = Order(**order.dict())
        # add the order to the db
        print(new_order.dict())
        inserted_order = order_collection.insert_one(new_order.dict())
        if inserted_order.acknowledged:
            return new_order
        else:
            raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail="Order creating failed")
    else: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong user")


@app.get("/orders", summary="This endpoint list all the orders of the current user")
def viewOrders(user: User = Depends(get_current_user)):
    order_collection = db_client.sender.order 
    try: 
        print(user.email)
        results = order_collection.find({"owner_email": user.email})
        # get all the orders of the current user 

        return [Order(**result) for result in results]
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.put("/orders/{tracking_id}/cancel", summary="This endpoint is responsible for cancelling a users order")
def cancelOrder(tracking_id: str, user: User = Depends(get_current_user)):
    # this endpoint will first check if the order those exist in the database 
    orderCollection = db_client.sender.order
    order = orderCollection.find_one({"tracking_id": tracking_id})
    if order:
        # if the order is not null, meaning exists in the database then
        # update the status of the order to cancelled
        order_update = UpdateOrderStatusModel(status=OrderState.cancelled, update_message="Order has been cancelled")
        order_status = orderCollection.update_one({"tracking_id": tracking_id}, {"$set": order_update.dict()})
        if order_status.acknowledged:
            # the update process occurred successfully
            return {"status": "order has been successfully cancelled"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error occurred during cancel operation")
        
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")