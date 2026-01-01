from fastapi import APIRouter
from app.api.v1 import ingredients, products, categories, daily_records, inventory, sales, transactions, dashboard, storage, mid_day_operations, reports

api_router = APIRouter()

api_router.include_router(ingredients.router, prefix="/ingredients", tags=["Skladniki"])
api_router.include_router(products.router, prefix="/products", tags=["Produkty"])
api_router.include_router(categories.router, prefix="/categories", tags=["Kategorie wydatkow"])
api_router.include_router(daily_records.router, prefix="/daily-records", tags=["Operacje dzienne"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Magazyn - snapshoty dzienne"])
api_router.include_router(storage.router, prefix="/storage", tags=["Magazyn - zliczenia"])
api_router.include_router(mid_day_operations.router, prefix="", tags=["Operacje w ciagu dnia"])
api_router.include_router(sales.router, prefix="/sales", tags=["Sprzedaz"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transakcje"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Pulpit"])
api_router.include_router(reports.router, prefix="/reports", tags=["Raporty"])
