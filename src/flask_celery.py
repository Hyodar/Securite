
from celery import Celery
from celery import Task

def make_celery(server):
    celery = Celery(server.import_name, broker=server.config['CELERY_BROKER_URL'], backend=server.config['CELERY_BACKEND'])
    celery.conf.update(server.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with server.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery