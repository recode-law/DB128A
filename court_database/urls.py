from django.urls import path

from .views import (CourtListView, CourtDetailView, submit_positive_feedback, submit_negative_feedback,
                    CreateDetailedFeedbackFormView, APIInfoView, rest_api_court, rest_api_court_search,
                    rest_api_court_percentage, rest_api_court_detail, rest_api_court_type, rest_api_state,
                    rest_api_court_feedback, rest_api_court_detailed_feedback, rest_api_rejection_reason,
                    rest_api_camera_perspective, rest_api_conferencing_software)

urlpatterns = [
    path("", CourtListView.as_view(), name="court-database-root"),
    path("court/<int:pk>", CourtDetailView.as_view(), name="court-database-court-detail"),
    path("court/<int:court_id>/good", submit_positive_feedback, name="court-database-good-feedback"),
    path("court/<int:court_id>/bad", submit_negative_feedback, name="court-database-bad-feedback"),
    path("court/<int:court_id>/feedback", CreateDetailedFeedbackFormView.as_view(), name="court-database-create-detailed-feedback"),
    path("api_info", APIInfoView.as_view(), name="court-database-api-info"),
    path("api/v1/court", rest_api_court, name="court-database-restapi-court"),
    path("api/v1/court/search", rest_api_court_search, name="court-database-restapi-court-search"),
    path("api/v1/court/percentage", rest_api_court_percentage, name="court-database-restapi-court-percentage"),
    path("api/v1/court/detail", rest_api_court_detail, name="court-database-restapi-court-detail"),
    path("api/v1/court_type", rest_api_court_type, name="court-database-restapi-court-type"),
    path("api/v1/state", rest_api_state, name="court-database-restapi-state"),
    path("api/v1/feedback", rest_api_court_feedback, name="court-database-restapi-feedback"),
    path("api/v1/feedback/detailed", rest_api_court_detailed_feedback, name="court-database-restapi-detailed-feedback"),
    path("api/v1/feedback/rejection_reason", rest_api_rejection_reason, name="court-database-restapi-rejection-reason"),
    path("api/v1/feedback/camera_perspective", rest_api_camera_perspective, name="court-database-restapi-camera-perspective"),
    path("api/v1/feedback/conferencing_software", rest_api_conferencing_software, name="court-database-restapi-conferencing-software"),
]
