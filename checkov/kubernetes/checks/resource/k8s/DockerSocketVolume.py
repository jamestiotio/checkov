
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class DockerSocketVolume(BaseK8Check):

    def __init__(self):
        name = "Do not expose the docker daemon socket to containers"
        # Exposing the socket gives container information and increases risk of exploit
        # read-only is not a solution but only makes it harder to exploit.
        # Location: Pod.spec.volumes[].hostPath.path
        # Location: CronJob.spec.jobTemplate.spec.template.spec.volumes[].hostPath.path
        # Location: *.spec.template.spec.volumes[].hostPath.path
        id = "CKV_K8S_27"
        supported_kind = ['Pod', 'Deployment', 'DaemonSet', 'StatefulSet', 'ReplicaSet', 'ReplicationController', 'Job', 'CronJob']
        categories = [CheckCategories.KUBERNETES]
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf):
        spec = {}

        if conf['kind'] == 'Pod':
            if "spec" in conf:
                spec = conf["spec"]
        elif conf['kind'] == 'CronJob':
            if "spec" in conf and "jobTemplate" in conf["spec"]:
                job_template_spec = conf["spec"]["jobTemplate"].get("spec")
                if job_template_spec and "template" in job_template_spec and "spec" in job_template_spec["template"]:
                    spec = job_template_spec["template"]["spec"]
        else:
            inner_spec = self.get_inner_entry(conf, "spec")
            spec = inner_spec if inner_spec else spec

        # Evaluate volumes
        if spec:
            volumes = spec.get("volumes", [])
            if not isinstance(volumes, list):
                return CheckResult.UNKNOWN
            for v in volumes:
                if not v.get("hostPath"):
                    continue
                if v["hostPath"].get("path") == "/var/run/docker.sock":
                    return CheckResult.FAILED
        return CheckResult.PASSED

check = DockerSocketVolume()
