
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/health")
# async def read_h():
#     return {"Hello": "World"}

# @app.get("/")
# async def read_root():
#     return {"pid": "or"}

from fastapi import FastAPI, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel, Field #field нужен будет для указания значения по умолчанию для атрибута и его допустимой длины
from datetime import datetime

app = FastAPI()

start_task_id = 1

tasks: list[dict] = []

class Task(BaseModel): # класс объектов "задания"
    id:int
    title:str = Field(min_length=3, max_length=1000) 
    description: Optional[str] = Field(default=None, max_length=1000)
    status:str = "new"
    created_at: datetime 

class TaskCreate(BaseModel):  #класс, на основе которого будут приниматься данные от пользователя
    title:str = Field(min_length=3, max_length=1000) 
    description: Optional[str] = Field(default=None, max_length=1000)

    

@app.post("/tasks")   # делаем POST-запрос чтобы создавать какую-то определенную задачу на основе ранее созданного класса TaskCreate
async def add_task (task_input: TaskCreate) -> Task:
    current_task_id = len(tasks)+1 #генерируем айди

    current_task = Task(
        id=current_task_id,
        title=task_input.title, 
        description=task_input.description, 
        status="new", 
        created_at=datetime.now()
    ) #создадим объект на основе изначального класса для задач Task
    tasks.append(current_task.model_dump()) #добавляем в изначальный список задач tasks объект, преобразованный в словарь как раз-таки с помощью model_dump()
    
    return current_task #возвращаем клиенту именно объект

@app.get("/tasks")  #делаем GET-запрос
async def get_tasks ():
    return tasks #возвращаем изначальный список, куда добавляются созданные задачи