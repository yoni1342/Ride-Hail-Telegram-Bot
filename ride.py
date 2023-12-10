import asyncio
from datetime import datetime, timedelta
import logging
import random
import sys

import redis
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    Chat,
    CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


API_TOKEN = '6451596541:AAH_bY-qfyf8JhKPyepSJxsE8yUg4TPgE80'


REDIS_CLOUD_HOST = 'redis-12596.c281.us-east-1-2.ec2.redns.redis-cloud.com'
REDIS_CLOUD_PORT = 12596
REDIS_CLOUD_PASSWORD = '91ta9nz2xJjVeQ8O3GopPfTep393DXbE'

redis_conn = redis.StrictRedis(
    host=REDIS_CLOUD_HOST,
    port=REDIS_CLOUD_PORT,
    password=REDIS_CLOUD_PASSWORD,
    decode_responses=True,
    )

form_router = Router()

class Form(StatesGroup):
    Register = State()
    Contact_info = State()
    Role = State()
    EditProfile = State()
    EditFullname = State()
    EditPhoneNumber = State()
    EditRole = State()
    Menu_Passenger = State()
    Menu_Driver = State()
    Book = State()
    BookValidate = State()
    BookLocation = State()
    BookDestination = State()
    BookConfirm = State()
    BookCancel = State()
    DriverStatus = State()
    RideComplete = State()
    RideAccept = State()
    DriverReview = State()
    PassengerReview = State()
    Rating = State()


@form_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_key = f"user:{user_id}"

    if not redis_conn.exists(user_key):
        menu_Passenger = ReplyKeyboardMarkup(resize_keyboard=True,
            keyboard=[[KeyboardButton(text="Register")]])
        await state.set_state(Form.Register)
        await message.answer('''
                🚗 Welcome to RideHailBot! 🚀
Are you prepared to enjoy convenient rides at your fingertips? 🌟 We're here to enhance your journey and make it more seamless than ever! Whether you're commuting or exploring, RideHailBot has got you covered.

👋 First time here?
Let's kick things off! If you're eager to get started, simply hit the Register button
to set up your RideHailBot account. 📲✨

🌍🚀
            ''', reply_markup=menu_Passenger)
    else:
        menu_Passenger = get_menu_Passenger_markup()
        menu_Driver = get_menu_Driver_markup()

        user_data = redis_conn.hgetall(user_key)

        if user_data.get('role') == "driver":
            await message.answer(f"Welcome back, {user_data['name']}! What would you like to do today?", reply_markup=menu_Driver)
            await state.set_state(Form.Menu_Driver)
        else:
            await message.answer(f"Welcome back, {user_data['name']}! What would you like to do today?", reply_markup=menu_Passenger)
            await state.set_state(Form.Menu_Passenger)

@form_router.message(Form.Register, F.text.casefold() == "register")
async def process_Contact_info(message: Message, state: FSMContext):
    await state.set_state(Form.Contact_info)
    Contact = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[[KeyboardButton(text="Share Contact", request_contact=True)]])
    await message.answer("please share you contact info:", reply_markup=Contact)


@form_router.message(Form.Contact_info)
async def process_Contact_info(message: Message, state: FSMContext):
    name = phone = ''
    if message.contact and message.contact.phone_number:
        if message.contact.first_name:
            name = message.contact.first_name
        if message.contact.last_name:
            name += " " + message.contact.last_name
        phone = message.contact.phone_number

    await state.update_data(name=name, phone=phone)
    await state.set_state(Form.Role)
    menu_Passenger = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Driver")],
                    [KeyboardButton(text="Passenger")]
                ])
    await message.answer("Great! Lastly, please specify your role..", reply_markup=menu_Passenger)

    
@form_router.message(Form.Role, F.text.casefold() == "driver")
async def process_role(message: Message, state: FSMContext):
    await state.update_data(role='driver')
    user_data = await state.get_data()

    await register_user(message.from_user.id, user_data)
    await state.clear()
    await message.answer("Registration successful, you can press /start to use the bot", 
                             reply_markup=ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="/start")],
                ]))


@form_router.message(Form.Role, F.text.casefold() == "passenger")
async def process_role(message: Message, state: FSMContext):
    await state.update_data(role='passenger')
    user_data = await state.get_data()

    await register_user(message.from_user.id, user_data)
    await state.clear()
    await message.answer("Registration successful, you can press /start to use the bot", 
                             reply_markup=ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="/start")],
                ]))


async def register_user(id, data):
    user_key = f"user:{id}"
    name = data['name']
    phone = data['phone']
    role = data['role']
    redis_conn.hset(user_key, mapping= {
        'id': id,
        "name": name,
        "phone": phone,
        "role": role,
        "status": "not available"
        })

async def get_user_by_id(id):
    user_key = f"user:{id}"
    user_data = redis_conn.hgetall(user_key)
    return user_data



def get_menu_Passenger_markup():
    menu_Passenger = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Book Ride")],
                    [KeyboardButton(text="Cancel Book")],
                    [KeyboardButton(text="View Book History")],
                    [KeyboardButton(text="Edit Profile")],
                    [KeyboardButton(text="Review")]
                ])
    return menu_Passenger

def get_menu_Driver_markup():
    menu_Driver = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="List Books")],
                    [KeyboardButton(text="Active Books")],
                    [KeyboardButton(text="Set Status")],
                    [KeyboardButton(text="View Book History")],
                    [KeyboardButton(text="Edit Profile")],
                    [KeyboardButton(text="Review")]
                ])
    return menu_Driver

def get_rating_markup():
    rating = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="1")],
                    [KeyboardButton(text="2")],
                    [KeyboardButton(text="3")],
                    [KeyboardButton(text="4")],
                    [KeyboardButton(text="5")]
                ]) 
    return rating

# Edit profile

@form_router.message(Form.Menu_Passenger, F.text.casefold() == "edit profile")
async def edit_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_key = f"user:{user_id}"
    
    if redis_conn.exists(user_key):
        await message.answer("You are about to edit your profile. Please choose what you want to edit:",
                             reply_markup=get_edit_profile_markup())
        await state.set_state(Form.EditProfile)
    else:
        await message.answer("You need to register first. Press register to continue.", 
                             reply_markup=ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Register")],
                ]))
        await state.set_state(Form.Register)     

def get_edit_profile_markup():
    menu_Passenger = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Full name")],
                    [KeyboardButton(text="Role")]
                ])
    return menu_Passenger

@form_router.message(Form.Menu_Driver, F.text.casefold() == "edit profile")
async def edit_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_key = f"user:{user_id}"
    
    if redis_conn.exists(user_key):
        await message.answer("You are about to edit your profile. Please choose what you want to edit:",
                             reply_markup=get_edit_profile_markup())
        await state.set_state(Form.EditProfile)
    else:
        await message.answer("You need to register first. Use /start to register.")

def get_edit_profile_markup():
    menu_Driver = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Full name")],
                    [KeyboardButton(text="Role")]
                ])
    return menu_Driver


@form_router.message(Form.EditProfile)
async def process_profile(message: Message, state: FSMContext):
    if message.text.casefold() == "full name":
        await message.answer("please provide your full name.")
        await state.set_state(Form.EditFullname)
    elif message.text.casefold() == "role":
        await message.answer("please provide your role.",reply_markup=ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Driver")],
                    [KeyboardButton(text="Passenger")]
                ]))
        await state.set_state(Form.EditRole)


@form_router.message(Form.EditFullname)
async def process_Contact_info(message: Message, state: FSMContext):
    Contact_info = message.text.strip()
    U_id = message.from_user.id
    user_key = f"user:{U_id}"
    redis_conn.hset(user_key, "name", Contact_info)
    await state.clear()
    menu = ''
    if redis_conn.hget(user_key, "role") == "driver":
        await state.set_state(Form.Menu_Driver)
        menu = get_menu_Driver_markup()
    else:
        await state.set_state(Form.Menu_Passenger)
        menu = get_menu_Passenger_markup()
    await message.answer("Your full name has been updated.", reply_markup=menu)
    

@form_router.message(Form.EditRole)
async def process_Contact_info(message: Message, state: FSMContext):
    role = message.text.casefold()
    U_id = message.from_user.id
    user_key = f"user:{U_id}"
    redis_conn.hset(user_key, "role", role)
    await state.clear()
    menu = ''
    if redis_conn.hget(user_key, "role") == "driver":
        await state.set_state(Form.Menu_Driver)
        menu = get_menu_Driver_markup()
    else:
        await state.set_state(Form.Menu_Passenger)
        menu = get_menu_Passenger_markup()
    await message.answer("Your role has been updated.", reply_markup=menu)



@form_router.message(Form.Menu_Passenger, F.text.casefold() == "book ride")
async def book(message: Message, state: FSMContext):
    await state.set_state(Form.BookLocation)
    Location = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[[KeyboardButton(text="Share Locaiton", request_location=True)]])
    await message.answer("please share you location:", reply_markup=Location)

@form_router.message(Form.BookLocation)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location = message.location.longitude)
    await state.set_state(Form.BookDestination)
    await message.answer("please share your destination:")


@form_router.message(Form.BookDestination)
async def process_destination(message: Message, state: FSMContext):
    await state.update_data(destination=message.text)
    menu_Passenger = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Confirm")],
                    [KeyboardButton(text="Cancel")]
                ])
    await message.answer("Please confirm your booking:", reply_markup=menu_Passenger)
    await state.set_state(Form.BookValidate)

curUser = None
curBookId = None


@form_router.message(Form.BookValidate, F.text.casefold() == "confirm")
async def process_confirm(message: Message, state: FSMContext):
    global curUser, curBookId
    await message.answer("Your booking has been confirmed!")
    await state.set_state(Form.Menu_Passenger)
    menu = get_menu_Passenger_markup()
    res = await estimate_time_distance()
    await message.answer(f"Estimated distance: {res[0]}")
    await message.answer(f"Estimated arrival time: {res[1]}", reply_markup=menu)
    curUser = message.from_user.id
    data = await state.get_data()
    store_key = "metric"
    store = redis_conn.hgetall(store_key)
    last_book_id = store.get("last_book_id", 0)
    book_key = f"book:{str(int(last_book_id) + 1)}"
    curBookId = str(int(last_book_id) + 1)
    redis_conn.hset(book_key, mapping = {
                "location": data["location"],
                "destination": data["destination"],
                "book_id": str(int(last_book_id) + 1),
                "status": "pending",
                "passenger_id": message.from_user.id,
                "driver_id": 0,
                "last_book_id": str(int(last_book_id) + 1)
            })
    redis_conn.hset(store_key, mapping={'last_book_id': str(int(last_book_id) + 1)})

    drivers = await get_all_drivers()
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    for driver_id in drivers:
        # await bot.send_message(chat_id=driver_id, text="New ride alert! Someone has booked a ride.")
        dat = str({
            "driver": driver_id,
            "passenger": curUser,
            "book_id": str(int(last_book_id) + 1)
        })
        builder = InlineKeyboardBuilder()
        builder.button(text="Accept", callback_data="accept")
        builder.button(text="Decline", callback_data="decline")
        builder.adjust(2,1)
        await bot.send_message(chat_id=driver_id, text="New ride alert! Someone has booked a ride.", reply_markup=builder.as_markup())

@form_router.callback_query(lambda c: c.data in ["accept", "decline"])
async def option_handler(callback_query: CallbackQuery, state: FSMContext, ):
    print(callback_query)
    curDriver = callback_query.from_user.id
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    if callback_query.data != "decline":
        menu = get_menu_Driver_markup()
        await state.set_state(Form.Menu_Driver)
        await bot.send_message(chat_id=curDriver, text="You have accepted the ride!", reply_markup=menu)
        redis_conn.hset(curBookId, 'status', 'accepted')
        redis_conn.hset(curBookId, 'driver_id', curDriver)
        await bot.send_message(chat_id=curUser, text="Your ride has been accepted. Please wait for the driver to arrive.")
        user_data = await get_user_by_id(curDriver)
        contact_phone_number = user_data['phone']
        contact_first_name = user_data['name']
        await bot.send_contact(
            chat_id=curUser,
            phone_number=contact_phone_number,
            first_name=contact_first_name
        )

        user_data = await get_user_by_id(curUser)
        contact_phone_number = user_data['phone']
        contact_first_name = user_data['name']
        await bot.send_contact(
            chat_id=curDriver,
            phone_number=contact_phone_number,
            first_name=contact_first_name
        )
    else:
        menu = get_menu_Driver_markup()
        await state.set_state(Form.Menu_Driver)
    await bot.delete_message(chat_id=user_id, message_id=message_id)



@form_router.message(Form.BookValidate, F.text.casefold() == "cancel")
async def process_cancel(message: Message, state: FSMContext):
    menu = get_menu_Passenger_markup()
    await state.set_state(Form.Menu_Passenger)
    await message.answer("Your booking has been cancelled!", reply_markup=menu)
    

@form_router.message(Form.Menu_Passenger, F.text.casefold() == "cancel book")
async def process_cancel(message: Message, state: FSMContext):
    u_id = message.from_user.id
    books = redis_conn.keys("book:*")
    menu = get_menu_Passenger_markup()
    await state.set_state(Form.Menu_Passenger)
    if len(books) == 0:
        await message.answer("You didn't have any books.", reply_markup=menu)
    else:
        found = False
        bok = ''
        for bk in books:
            book_data = redis_conn.hgetall(bk)
            if book_data.get('passenger_id') == u_id and (book_data.get('status') == 'pending' or book_data.get('status') == 'accepted'):
                if book_data.get('status') == 'accepted':
                    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
                    await bot.send_message(chat_id=book_data.get('driver_id'), text="Your ride has been cancelled. please check your active books.")
                redis_conn.hset(bk, 'status', 'cancelled')
                found = True
                bok = bk
                break

        if not found:
            print("not found")
            await message.answer("You didn't have any active or pending books.", reply_markup=menu)
        else:
            redis_conn.delete(bok)
            await message.answer("Your booking has been cancelled!", reply_markup=menu)


# see all books - Driver

@form_router.message(Form.Menu_Driver, F.text.casefold() == "list books")
async def list_books(message: Message, state: FSMContext):
    books = redis_conn.keys("book:*")
    if len(books) == 0:
        await message.answer("There are no books at the moment.")
    else:
        Keys = []
        for book in books:
            book_data = redis_conn.hgetall(book)
            button = KeyboardButton(text=f"Book Id: {book_data['book_id']}\nLocation: {book_data['location']}\nDestination: {book_data['destination']}")
            if book_data['status'] == "pending":
                Keys.append(button)
        keyBoard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[Keys])
        if len(Keys) == 0:
            await message.answer("There are no books at the moment.")
        else:
            await message.answer("Here are the list of books:", reply_markup=keyBoard)
            await state.set_state(Form.RideAccept)


# set status - Driver

@form_router.message(Form.Menu_Driver, F.text.casefold() == "set status")
async def set_status(message: Message, state: FSMContext):
    menu_Driver = ReplyKeyboardMarkup(resize_keyboard=True,
        keyboard=[
                    [KeyboardButton(text="Available")],
                    [KeyboardButton(text="Not Available")]
                ])
    await message.answer("Please set your status:", reply_markup=menu_Driver)
    await state.set_state(Form.DriverStatus)


@form_router.message(Form.DriverStatus, F.text.casefold() == "available")
async def set_status(message: Message, state: FSMContext):
    menu = get_menu_Driver_markup()
    await state.set_state(Form.Menu_Driver)
    await message.answer("Your status has been set to available.", reply_markup=menu)
    id = message.from_user.id
    user_key = f"user:{id}"
    redis_conn.hset(user_key, "status", "available")

@form_router.message(Form.DriverStatus, F.text.casefold() == "not available")
async def set_status(message: Message, state: FSMContext):
    menu = get_menu_Driver_markup()
    await state.set_state(Form.Menu_Driver)
    await message.answer("Your status has been set to not available.", reply_markup=menu)
    id = message.from_user.id
    user_key = f"user:{id}"
    redis_conn.hset(user_key, "status", "not available")



# see active books - Driver

@form_router.message(Form.Menu_Driver, F.text.casefold() == "active books")
async def list_books(message: Message, state: FSMContext):
    books = redis_conn.keys("book:*")
    if len(books) == 0:
        await message.answer("There are no books at the moment.")
    else:
        Keys = []
        for book in books:
            book_data = redis_conn.hgetall(book)
            button = KeyboardButton(text=f"Book Id: {book_data['book_id']}\nLocation: {book_data['location']}\nDestination: {book_data['destination']}")
            if book_data['status'] == "accepted" and book_data['driver_id'] == str(message.from_user.id):
                Keys.append(button)
        keyBoard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[Keys])
        if len(Keys) == 0:
            await message.answer("There are no active books at the moment.")
        else:
            await message.answer("Here are the list of active books waiting for you:", reply_markup=keyBoard)
            await state.set_state(Form.RideComplete)


# accept ride - Driver
@form_router.message(Form.RideAccept)
async def process_accept(message: Message, state: FSMContext):
    menu = get_menu_Driver_markup()
    await state.set_state(Form.Menu_Driver)
    await message.answer("You have accepted the ride!", reply_markup=menu)
    id = message.from_user.id
    book_id = message.text.split("\n")[0].split(":")[1].strip()
    book_key = f"book:{book_id}"
    print("book key", book_key)
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    book = redis_conn.hgetall(book_key)
    pass_id = book['passenger_id']
    redis_conn.hset(book_key, 'status', 'accepted')
    redis_conn.hset(book_key, 'driver_id', id)
    await bot.send_message(chat_id=pass_id, text="Your ride has been accepted. Please wait for the driver to arrive.")


# complete book - Driver

@form_router.message(Form.RideComplete)
async def process_complete(message: Message, state: FSMContext):
    menu = get_menu_Driver_markup()
    await state.set_state(Form.Menu_Driver)
    await message.answer("Thank you for riding with us! We hope to see you again soon.", reply_markup=menu)
    id = message.from_user.id
    book_id = message.text.split("\n")[0].split(":")[1].strip()
    book_key = f"book:{book_id}"
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    book = redis_conn.hgetall(book_key)
    passenger_id = book["passenger_id"]
    redis_conn.hset(book_key, 'status', 'completed')
    await bot.send_message(chat_id=passenger_id, text="Your ride has been completed. Thank you for riding with us!")



# Review Drivers

@form_router.message(Form.Menu_Passenger, F.text.casefold() == "review")
async def review(message: Message, state: FSMContext):
    drivers = await get_all_drivers()
    Key = []
    for driver_id in drivers:
        user_key = f"user:{driver_id}"
        user_data = redis_conn.hgetall(user_key)
        Key.append(KeyboardButton(text=f"Driver Id: {driver_id}\nName: {user_data['name']}\nPhone: {user_data['phone']}"))
    
    keyBoard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[Key])
    await message.answer("Please choose a driver to review:", reply_markup=keyBoard)
    await state.set_state(Form.DriverReview)
    
@form_router.message(Form.Menu_Driver, F.text.casefold() == "review")
async def review(message: Message, state: FSMContext):
    passengers = await get_all_passengers()
    Key = []
    for passenger_id in passengers:
        user_key = f"user:{passenger_id}"
        user_data = redis_conn.hgetall(user_key)
        Key.append(KeyboardButton(text=f"Passenger Id: {passenger_id}\nName: {user_data['name']}\nPhone: {user_data['phone']}"))
    
    keyBoard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[Key])
    await message.answer("Please choose a passenger to review:", reply_markup=keyBoard)
    await state.set_state(Form.PassengerReview)


@form_router.message(Form.DriverReview)
async def process_review(message: Message, state: FSMContext):
    rating = get_rating_markup()
    reviewee_id = message.text.split("\n")[0].split(":")[1].strip()
    await state.update_data(reviewee = reviewee_id)
    if redis_conn.exists(f"rating:{message.from_user.id}:{reviewee_id}"):
        menu = ''
        user_key = f'user:{message.from_user.id}'
        user_data = redis_conn.hgetall(user_key)
        await state.clear()
        
        if user_data.get('role') == "driver":
            menu = get_menu_Driver_markup()
            await state.set_state(Form.Menu_Driver)
        else:
            menu = get_menu_Passenger_markup()
            await state.set_state(Form.Menu_Passenger)

        await message.answer("You have already reviewed this user.", reply_markup=menu)
    else:
        await message.answer("Please rate the driver from 1-5:", reply_markup=rating)
        await state.set_state(Form.Rating)


@form_router.message(Form.PassengerReview)
async def process_review(message: Message, state: FSMContext):
    rating = get_rating_markup()
    reviewee_id = message.text.split("\n")[0].split(":")[1].strip()
    await state.update_data(reviewee = reviewee_id)
    if redis_conn.exists(f"rating:{message.from_user.id}:{reviewee_id}"):
        menu = ''
        user_key = f'user:{message.from_user.id}'
        user_data = redis_conn.hgetall(user_key)
        await state.clear()
        
        if user_data.get('role') == "driver":
            menu = get_menu_Driver_markup()
            await state.set_state(Form.Menu_Driver)
        else:
            menu = get_menu_Passenger_markup()
            await state.set_state(Form.Menu_Passenger)

        await message.answer("You have already reviewed this user.", reply_markup=menu)
    await message.answer("Please rate the passenger from 1-5:", reply_markup=rating)
    await state.set_state(Form.Rating)


@form_router.message(Form.Rating)
async def process_rating(message: Message, state: FSMContext):
    reviewer_id = message.from_user.id
    data = await state.get_data()
    reviewee_id = data['reviewee']
    rating_key = f"rating:{reviewer_id}:{reviewee_id}"
    menu = ''
    user_key = f'user:{reviewer_id}'
    user_data = redis_conn.hgetall(user_key)
    await state.clear()
    
    if user_data.get('role') == "driver":
        menu = get_menu_Driver_markup()
        await state.set_state(Form.Menu_Driver)
    else:
        menu = get_menu_Passenger_markup()
        await state.set_state(Form.Menu_Passenger)

    await message.answer("Thank you for your feedback!", reply_markup=menu)
    redis_conn.hset(rating_key, "rating", message.text.strip())


# View Book History - driver

@form_router.message(Form.Menu_Driver, F.text.casefold() == "view book history")
async def view_book_history(message: Message, state: FSMContext):
    books = redis_conn.keys("book:*")
    if len(books) == 0:
        await message.answer("There are no books at the moment.")
    else:
        Keys = []
        
        for book in books:
            book_data = redis_conn.hgetall(book)
            button = KeyboardButton(text=f"Book Id: {book_data['book_id']}\nLocation: {book_data['location']}\nDestination: {book_data['destination']}")
            if book_data['driver_id'] == str(message.from_user.id) and book_data['status'] == "completed":
                Keys.append(button)
        
        if len(Keys) == 0:
            await message.answer("There are no books at the moment.")
        else:
            await message.answer("Here are the list of books you have completed:")
            for key in Keys:
                await message.answer(key.text + "\n")

        menu = get_menu_Driver_markup()
        await state.set_state(Form.Menu_Driver)
        


# View Book History - passenger
@form_router.message(Form.Menu_Passenger, F.text.casefold() == "view book history")
async def view_book_history(message: Message, state: FSMContext):
    books = redis_conn.keys("book:*")
    if len(books) == 0:
        await message.answer("There are no books at the moment.")
    else:
        Keys = []
        for book in books:
            book_data = redis_conn.hgetall(book)
            button = KeyboardButton(text=f"Book Id: {book_data['book_id']}\nLocation: {book_data['location']}\nDestination: {book_data['destination']}")
            if book_data['passenger_id'] == str(message.from_user.id) and book_data['status'] == "completed":
                Keys.append(button)
        
        if len(Keys) == 0:
            await message.answer("There are no books at the moment.")
        else:
            await message.answer("Here are the list of books you have completed:")
            for key in Keys:
                await message.answer(key.text + "\n")
        
        menu = get_menu_Passenger_markup()
        await state.set_state(Form.Menu_Passenger)


async def estimate_time_distance():
    distance = random.randint(5, 100)
    curr = datetime.now()
    minu = random.randint(1, 60)
    delta = timedelta(minutes=minu)
    estim = curr + delta
    return distance, estim.strftime("%I:%M %p")

async def get_all_drivers():
    drivers = []
    all_keys = redis_conn.keys("user:*")
    
    for key in all_keys:
        user_data = redis_conn.hgetall(key)
        if user_data.get("role") == "driver":
            drivers.append(int(user_data["id"]))

    return drivers

async def get_all_passengers():
    passengers = []
    all_keys = redis_conn.keys("user:*")
    
    for key in all_keys:
        user_data = redis_conn.hgetall(key)
        if user_data.get("role") == "passenger":
            passengers.append(int(user_data["id"]))

    return passengers

async def main():
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    logging.basicConfig(level=logging.INFO)
    dp.include_router(form_router)

    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())