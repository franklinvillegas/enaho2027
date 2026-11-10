from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view(), name="csrf"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/yo/", views.YoView.as_view(), name="yo"),
    path("catalogos/odeis/", views.OdeisView.as_view(), name="odeis"),
    path("registro-uso/", views.RegistroUsoView.as_view(), name="registro-uso"),
]
