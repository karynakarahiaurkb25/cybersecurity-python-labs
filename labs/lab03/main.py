from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from labs.lab03.config import VALUE_THRESHOLD, VALUE_UNIT, VARIANT_NAME
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=f"Сервіс: {VARIANT_NAME}",
    description=f"Предметна область: {VARIANT_NAME}. Одиниця: {VALUE_UNIT}. Поріг: {VALUE_THRESHOLD}",
    lifespan=lifespan,
)

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["Системні"])
def ping():
    return {"status": "ok"}


@app.get("/student", tags=["Системні"])
def get_student_info():
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }