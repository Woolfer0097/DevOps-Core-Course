import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
yc_config = pulumi.Config("yandex")

zone = config.get("zone") or "ru-central1-a"
vm_user = config.get("vm_user") or "ubuntu"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"

with open(ssh_public_key_path.replace("~", __import__("os").path.expanduser("~"))) as f:
    ssh_public_key = f.read().strip()

network = yandex.get_vpc_network(name="default")
subnet = yandex.get_vpc_subnet(name="default-ru-central1-a")

security_group = yandex.VpcSecurityGroup(
    "lab-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="SSH",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="HTTP",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="App",
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound",
        ),
    ],
)

image = yandex.get_compute_image(family="ubuntu-2404-lts-oslogin")

instance = yandex.ComputeInstance(
    "lab-vm",
    platform_id="standard-v2",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,  # type: ignore[arg-type]
            nat=True,
            security_group_ids=[security_group.id],
        ),
    ],
    metadata={
        "ssh-keys": f"{vm_user}:{ssh_public_key}",
    },
    labels={
        "project": "devops-lab04",
        "tool": "pulumi",
    },
)

pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", instance.network_interfaces[0].ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("ssh_command", instance.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {vm_user}@{ip}"
))
