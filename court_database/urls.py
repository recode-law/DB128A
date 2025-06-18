from django.urls import path

from .views import (CourtListView, CourtDetailView, submit_positive_feedback, submit_negative_feedback,
                    CreateDetailedFeedbackFormView, APIInfoView, rest_api_court, rest_api_court_detail,
                    rest_api_court_type, rest_api_state)

urlpatterns = [
    path("", CourtListView.as_view(), name="court-database-root"),
    path("court/<int:pk>", CourtDetailView.as_view(), name="court-database-court-detail"),
    path("court/<int:court_id>/good", submit_positive_feedback, name="court-database-good-feedback"),
    path("court/<int:court_id>/bad", submit_negative_feedback, name="court-database-bad-feedback"),
    path("court/<int:court_id>/feedback", CreateDetailedFeedbackFormView.as_view(), name="court-database-create-detailed-feedback"),
    path("api_info", APIInfoView.as_view(), name="court-database-api-info"),
    path("api/v1/court", rest_api_court, name="court-database-restapi-court"),
    path("api/v1/court/detail", rest_api_court_detail, name="court-database-restapi-court-detail"),
    path("api/v1/court_type", rest_api_court_type, name="court-database-restapi-court-type"),
    path("api/v1/state", rest_api_state, name="court-database-restapi-state")
]
