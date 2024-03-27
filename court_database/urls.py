from django.urls import path

from .views import CourtListView, CourtDetailView, submit_positive_feedback, submit_negative_feedback, CreateDetailedFeedbackFormView

urlpatterns = [
    path("", CourtListView.as_view(), name="court-database-root"),
    path("court/<int:pk>", CourtDetailView.as_view(), name="court-database-court-detail"),
    path("court/<int:court_id>/good", submit_positive_feedback, name="court-database-good-feedback"),
    path("court/<int:court_id>/bad", submit_negative_feedback, name="court-database-bad-feedback"),
    path("court/<int:court_id>/feedback", CreateDetailedFeedbackFormView.as_view(), name="court-database-create-detailed-feedback")
]
