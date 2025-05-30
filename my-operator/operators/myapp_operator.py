import kopf
import kubernetes.client
import logging
from kubernetes.client.rest import ApiException

# 配置日志
logging.basicConfig(level=logging.INFO)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.INFO
    settings.watching.server_timeout = 60


@kopf.on.create('example.com', 'v1alpha1', 'myapps')
def create_fn(spec, name, namespace, logger, **kwargs):
    logger.info(f"Creating application: {name} in {namespace}")

    # 创建关联资源
    create_deployment(spec, name, namespace, logger)
    create_service(spec, name, namespace, logger)

    return {'message': f'App {name} created with {spec["replicas"]} replicas'}


def create_deployment(spec, name, namespace, logger):
    api = kubernetes.client.AppsV1Api()

    deployment = {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': name,
            'labels': {'app': name}
        },
        'spec': {
            'replicas': spec.get('replicas', 1),
            'selector': {'matchLabels': {'app': name}},
            'template': {
                'metadata': {'labels': {'app': name}},
                'spec': {
                    'containers': [{
                        'name': name,
                        'image': spec['image'],
                        'ports': [{'containerPort': 80}]
                    }]
                }
            }
        }
    }

    try:
        api.create_namespaced_deployment(namespace, deployment)
        logger.info(f"Deployment created: {name}")
    except ApiException as e:
        logger.error(f"Deployment creation failed: {e}")
        raise kopf.PermanentError(f"API error: {e.reason}")


def create_service(spec, name, namespace, logger):
    api = kubernetes.client.CoreV1Api()

    service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {'name': name},
        'spec': {
            'selector': {'app': name},
            'ports': [{'port': 80, 'targetPort': 80}],
            'type': 'ClusterIP'
        }
    }

    try:
        api.create_namespaced_service(namespace, service)
        logger.info(f"Service created: {name}")
    except ApiException as e:
        logger.error(f"Service creation failed: {e}")
        # 不需要终止，Operator 可以继续运行


@kopf.on.delete('example.com', 'v1alpha1', 'myapps')
def delete_fn(name, namespace, logger, **kwargs):
    logger.info(f"Deleting application: {name}")
    # Kubernetes 垃圾回收会自动删除关联资源
    return {'message': 'Application marked for deletion'}


if __name__ == '__main__':
    # 本地运行模式
    kopf.run()