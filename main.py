from enum import Enum
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict
from pydantic import BaseModel, Field #field нужен будет для указания значения по умолчанию для атрибута и его допустимой длины
from datetime import datetime

app = FastAPI()

start_task_id = 1

tasks: list[dict] = []

class TaskSortBy(str, Enum): #добавляем класс, по чему у нас могут сортироваться задачи
    CREATED_AT = "created_at" #соответсвенно по времени создания
    UPDATED_AT = "updated_at" #по времени обновления
    TITLE = "title" #по названию

class SortOrder(str, Enum): #этот класс добавляем для возможности выбора "направления" сортировки
    ASC = "asc"   # По возрастанию (A-Z, от старых к новым)
    DESC = "desc" # По убыванию (Z-A, от новых к старым)


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
async def get_tasks (
    status: Optional[TaskStatus] = None, #необязательный параметр 'статус' по умолчанию равен None
    search: Optional[str] = None, #необязательный параметр для поиска
    sort_by: TaskSortBy = TaskSortBy.CREATED_AT, #параметр сортировки, по умолчанию по времени создания
    order: SortOrder = SortOrder.ASC, #параметр задания направления сортировки, по умолчанию по возрастанию
    limit: int = Query(default=10,ge=1,le=100), #сколько задач должно быть на одной странице
    offset: int = Query(default=0,ge=0), #сколько задач с начала мы пропускаем и не показываем
):
    if status is None: #то есть если статус не был передан, то ничего не меняется и преедается просто список всех задач
        result = list(tasks)
    else:
        result = [task for task in tasks if task["status"] == status] #генератор списка с фильтром по статусу
    #далее начинается регистронезависимый поиск
    if search is not None:
        search_lower = search.lower() # приведение поискового запроса к нижнему регистру

        filtered_by_search = []
        for task in result:

            #Приводим  title (название задачи) к нижнему регистру (для сравнения с поисковым запросом)
            title_match = search_lower in task["title"].lower() #проверяет содержится ли поисковой запрос в нижнем регистре в навзании задачи в нижнем регистре

            desc_match = False #эта строка нужна, потому что descriprion необазательное поле и может быть равно None

            if task["description"] is not None:
                desc_match = search_lower in task["description"].lower() #проверяет содержится ли поисковой запрос в нижнем регистре в описании задачи в нижнем регистре

            if title_match or desc_match: #если либо название либо описание True (совпало с поиском)
                filtered_by_search.append(task) #тогда добавляем задачу в новый список
        result = filtered_by_search

#далее пойдет сортировка
    is_reverse = (order == SortOrder.DESC) #эта переменная будет принимать значение True, если пользователем был выбран DESC (обратное направление)

    if sort_by == TaskSortBy.UPDATED_AT: #если сортировка идет по времени обновления

        #время обновления необязательный параметр, который может быть равен None,
        #для чего и создается такое условие, согласно которому, если оно равно None,
        #чтобы оно становилось просто минимальным временем и было в конце списка (datetime.min),
        #а revers отвечает в методе .sort как-раз таки за направление сортировки, и туда мы
        #передаем нашу переменную-флаг is_reverse
        result.sort(key=lambda x: x.get("updated_at") or datetime.min, reverse=is_reverse)

    else:
        #если же сортировка идет по названию или времени создания,
        #которые являются обязательными параметрами и всегда есть:
        result.sort(key=lambda x: x[sort_by.value], reverse=is_reverse)

    #здесь пагинация
    result = result[offset : offset + limit]

    return result
         
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

# Указываем status_code=204, чтобы сервер возвращал пустой ответ при успехе
@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    for task in tasks:
        # Ищем нужную задачу по айди в списке
        if task["id"] == task_id:
            # Удаляем задачу из списка
            tasks.remove(task)
            # Вместо return {"detail": ...} мы возвращаем None (или просто пишем return)
            return
            
    # Если цикл завершился и задача не найдена, отдаем 404
    raise HTTPException(status_code=404, detail=f"Задача с таким ID как {task_id} не существует")
