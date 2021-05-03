from ..models.transactions import Transaction as TransactionModel
from .base import app


@app.resource('/transactions')
class Transaction:
    model = TransactionModel
