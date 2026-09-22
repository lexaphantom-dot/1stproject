from enum import Enum
from fastapi import FastAPI, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel, Field #field нужен будет для указания значения по умолчанию для атрибута и его допустимой длины
from datetime import datetime

app = FastAPI()

start_task_id = 1

tasks: list[dict] = []

class TaskStatus(str, Enum): #класс для статусов
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(BaseModel): # класс объектов "задания"
    id:int
    title:str = Field(min_length=3, max_length=1000) 
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = TaskStatus.NEW #значение по умолчанию в enum
    created_at: datetime
    updated_at: Optional[datetime] = None

class TaskCreate(BaseModel):  #класс, на основе которого будут приниматься данные от пользователя
    title:str = Field(min_length=3, max_length=1000) 
    description: Optional[str] = Field(default=None, max_length=1000)

class TaskUpdate(BaseModel):
    title: Optional[str] = Field (default = None, min_length = 3, max_length = 1000)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatus] = Field(default=None) #также используем enum

   
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

#переходим к Заданию №2

@app.get ("/tasks/{task_id}", response_model=Task) #создание функции получения задачи по определенному айди
async def get_task_by_id (task_id:int):
    for task in tasks:
        if task["id"] == task_id:
            return task #здесь благодаря response_model FastAPI автоматически преобразует словарь в модель Task, указанную ранее в самом начале
        
    raise HTTPException(status_code=404, detail=f"Задача с таким ID как {task_id} не существует")

@app.patch("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id: #ищем задачу с нужным айди
            update_data = task_update.model_dump(exclude_unset=True)

            changes = False #специальная переменная-флаг

            #создается словарь только с теми данными, что обновил клиент
            for key, value in update_data.items():
            #обновление ключей
                if task[key] != value: #если значение неравно старому (то есть поменялось)
                    task[key] = value  #значит обновляем его
                    changes = True #меняем нашу переменную-флаг
            if changes: #соответственно если наш флаг поменялся на true, что означает что у нас поменялась задача, значит меняем время обновления
                task["updated_at"] = datetime.now()
            return task #возвращение задачи с обновленными полями (и возможно новым временем обновления)
    raise HTTPException(status_code=404, detail=f"Задача с таким ID как {task_id} не существует")