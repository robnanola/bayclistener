from django.http import JsonResponse
from django.views import View
from .models import TransferEvent

class TransferHistoryView(View):
    def get(self, request, token_id):
        events = TransferEvent.objects.filter(token_id=token_id).values()
        return JsonResponse(list(events), safe=False)
