from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import FeedbackQuestion
from .services import FeedbackService


@login_required
def question_active(request, fonctionnalite):
    """
    Appelée en fetch() depuis le dashboard. Renvoie {"html": None} si rien à
    montrer, sinon {"html": "<div class='feedback-widget'>...</div>"}.
    """
    question = FeedbackService.should_show(request.user, fonctionnalite)
    if not question:
        return JsonResponse({"html": None})

    FeedbackService.marquer_affichee(request.user, question)
    html = render_to_string("feedback/_widget_question.html", {"question": question}, request=request)
    return JsonResponse({"html": html})


@login_required
@require_POST
def repondre(request, question_id):
    """
    Enregistre une réponse et renvoie soit la question de niveau suivant
    (ex: niveau 2 après un 👎), soit le message de remerciement.
    """
    question = get_object_or_404(FeedbackQuestion, pk=question_id, active=True)
    reponse = request.POST.get("reponse", "")
    commentaire = request.POST.get("commentaire", "")
    version = request.POST.get("version_application", "")

    FeedbackService.record_response(
        utilisateur=request.user,
        question=question,
        reponse=reponse,
        commentaire=commentaire,
        version_application=version,
    )

    suivante = FeedbackService.question_suivante(question, reponse)
    if suivante:
        html = render_to_string("feedback/_widget_question.html", {"question": suivante}, request=request)
    else:
        html = render_to_string("feedback/_widget_merci.html", {}, request=request)

    return JsonResponse({"html": html})
