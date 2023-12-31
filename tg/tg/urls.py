"""
URL configuration for tg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from req import views

import typing


pattern_with_params = r'/(%s)(\/)?(\?)?[a-zA-Z0-9\=\&]+'


def extend_path(name: str, handler: typing.Callable):
    return [
        path(name + i, handler)
        for i in ['', '/']
    ]


urlpatterns = []

urlpatterns.extend(
    extend_path(
        name = 'ping', 
        handler = views.ping,
    )
)

urlpatterns.extend(
    extend_path(
        name = 'message',
        handler = views.message,
    )
)

urlpatterns.extend(
    extend_path(
        name = 'file',
        handler = views.file,
    )
)

urlpatterns.extend(
    extend_path(
        name = 'user',
        handler = views.user,
    )
)
