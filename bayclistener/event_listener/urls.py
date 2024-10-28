from django.urls import path
from .views import TransferHistoryView

urlpatterns = [
    path('transfer-history/<str:token_id>/', TransferHistoryView.as_view(), name='transfer_history'),
]
