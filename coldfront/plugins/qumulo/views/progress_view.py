from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

import random

class ProgressView(View):

    def get(self, request, *args, **kwargs):

        progress = random.randint(0, 100)
        progress_data = {
            "status": "in_progress",
            "progress": progress,
        }

        return JsonResponse(progress_data)