from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def community(request):
    # Only logged-in users can view the community.
    return render(request, "community/community.html")