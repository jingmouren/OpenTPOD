# Development Notes

## Authentication

Using rest_auth and cvat's authentication

/auth/login/
/auth/logout/
...

## Test Account

tpod:admin-test

## CVAT workflow

To create a task:
POST /tasks: {name, labels, image_quality, z_order}, notice there is no slash in the end
POST /task/<pk>/data: form data binary
  * calling engine/views.py "task.create" in TaskViewSet-->data
  * calling engine/task.py _create_thread in rq
GET /task/<pk>/status 
DELETE /task/<pk>/status: when server encounters errors

Client-side DOM id: DashboardCreateContent

For the dashboard page:
/dashboard/meta
GET /tasks -- represents information for different tasks
/tasks/<task id>/frames/0 -- for a snapshot of the video

## TODO:

1. finish rest api first. add classifier, job APIs
2. write tests for these rest apis, combining both CVAT and opentpod.
  1. see CVAT's tests for example


## Changes to CVAT

- cvat/apps/engine/urls.py

```
    # entry point for API
    #  path('api/v1/', include((router.urls, 'cvat'), namespace='v1'))
    # (junjuew): changed to solve reverse lookup bug
    path('api/v1/', include((router.urls)))  # https://github.com/encode/django-rest-framework/issues/2760
```

-  cvat/apps/engine/static/engine/js/annotationUI.js

```
    // window.history.replaceState(null, null, `${window.location.origin}/?id=${jobData.id}`);
```
