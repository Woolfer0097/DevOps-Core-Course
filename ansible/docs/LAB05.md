# Lab 5 docs
## Check Connectivity
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible all -i inventory/hosts.ini -m ping
ansible webservers -i inventory/hosts.ini -a "uptime"
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
woolfer-vm | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
woolfer-vm | CHANGED | rc=0 >>
 20:53:28 up 24 min,  1 user,  load average: 0.00, 0.00, 0.00

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible all -m ping
ansible webservers -a "uname -a"
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
woolfer-vm | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
woolfer-vm | CHANGED | rc=0 >>
Linux fhmp5bm0a98con1e4kip 6.8.0-100-generic #100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

# LAB05 — Ansible Provisioning & Deployment

## 1. Architecture Overview

**Ansible Version**


woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible --version
ansible [core 2.19.0]
  config file = /home/woolfer0097/Code/DevOps-Core-Course1/ansible/ansible.cfg
  configured module search path = ['/home/woolfer0097/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3/dist-packages/ansible
  ansible collection location = /home/woolfer0097/.ansible/collections:/usr/share/ansible/collections
  executable location = /usr/bin/ansible
  python version = 3.13.7 (main, Jan 22 2026, 20:15:57) [GCC 15.2.0] (/usr/bin/python3)
  jinja version = 3.1.6
  pyyaml version = 6.0.2 (with libyaml v0.2.5)

**Target VM**

* OS: Ubuntu 22.04 LTS
* Python: 3.12
* Docker installed via role

**Role Structure**

```
roles/
 ├── common
 ├── docker
 └── app_deploy
```

**Why roles instead of monolithic playbooks?**
Roles separate concerns (system setup, Docker install, app deploy). This improves readability, reuse, and maintainability.

---

## 2. Roles Documentation

### common

**Purpose:**
Base system configuration (packages, apt cache, timezone).

**Variables:**

```yaml
common_packages:
common_timezone:
```

**Handlers:**
None.

**Dependencies:**
None.

---

### docker

**Purpose:**
Install Docker CE, configure repo, enable service, add user to docker group.

**Variables:**

```yaml
docker_packages:
docker_user:
docker_apt_repo:
```

**Handlers:**

* restart docker

**Dependencies:**
Depends logically on `common` (needs curl, gnupg).

---

### app_deploy

**Purpose:**
Authenticate to Docker Hub, pull image, run container, verify health.

**Variables:**

```yaml
dockerhub_username:
dockerhub_password:
app_name:
docker_image:
app_port:
```

**Handlers:**

* restart app container (if used)

**Dependencies:**
Requires Docker role to be executed first.

---

## 3. Idempotency Demonstration


## Idempotency Explanation

### First run:

-    apt cache → changed (cache updated)

-    package installs → changed (packages installed)

-    repo/key → changed (added)

-    docker service → changed (started/enabled)

-    user group → changed (user added)

###    Second run:

-    apt cache → ok (still valid due to cache_valid_time)

-    packages → ok (already installed, state=present)

-    repo/key → ok (already exists)

-    service → ok (already running/enabled)

-    user group → ok (already in group)

Why nothing changes second time:
All tasks use state-based modules (apt, service, user, apt_repository) that check current system state and only act if drift exists, achieving convergence to the desired state.

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/provision.yml -b

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
ok: [woolfer-vm]

TASK [common : Update apt cache] ************************************************************************************************************************
changed: [woolfer-vm]

TASK [common : Install common packages] *****************************************************************************************************************
changed: [woolfer-vm]

TASK [common : Set timezone] ****************************************************************************************************************************
changed: [woolfer-vm]

TASK [docker : Install dependencies for Docker repo] ****************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
changed: [woolfer-vm]

TASK [docker : Add Docker APT repository] ***************************************************************************************************************
changed: [woolfer-vm]

TASK [docker : Install Docker packages] *****************************************************************************************************************
changed: [woolfer-vm]

TASK [docker : Ensure Docker service is running and enabled] ********************************************************************************************
ok: [woolfer-vm]

TASK [docker : Add user to docker group] ****************************************************************************************************************
changed: [woolfer-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] *************************************************************************************
changed: [woolfer-vm]

RUNNING HANDLER [docker : restart docker] ***************************************************************************************************************
changed: [woolfer-vm]

PLAY RECAP **********************************************************************************************************************************************
woolfer-vm                 : ok=12   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/provision.yml -b

PLAY [Provision web servers] ****************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
ok: [woolfer-vm]

TASK [common : Update apt cache] ************************************************************************************************************************
ok: [woolfer-vm]

TASK [common : Install common packages] *****************************************************************************************************************
ok: [woolfer-vm]

TASK [common : Set timezone] ****************************************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Install dependencies for Docker repo] ****************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Add Docker GPG key] **********************************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Add Docker APT repository] ***************************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Install Docker packages] *****************************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Ensure Docker service is running and enabled] ********************************************************************************************
ok: [woolfer-vm]

TASK [docker : Add user to docker group] ****************************************************************************************************************
ok: [woolfer-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] *************************************************************************************
ok: [woolfer-vm]

PLAY RECAP **********************************************************************************************************************************************
woolfer-vm                 : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 


woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -b

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
ok: [woolfer-vm]

TASK [app_deploy : Login to Docker Hub] *****************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Pull application image] **************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Stop existing container if running] **************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Remove old container if exists] ******************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Run application container] ***********************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Wait for application port to be ready] ***********************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Verify health endpoint] **************************************************************************************************************
ok: [woolfer-vm]

RUNNING HANDLER [app_deploy : restart app container] ****************************************************************************************************
changed: [woolfer-vm]

PLAY RECAP **********************************************************************************************************************************************
woolfer-vm                 : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -b

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
ok: [woolfer-vm]

TASK [app_deploy : Login to Docker Hub] *****************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Pull application image] **************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Stop existing container if running] **************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Remove old container if exists] ******************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Run application container] ***********************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Wait for application port to be ready] ***********************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Verify health endpoint] **************************************************************************************************************
ok: [woolfer-vm]

RUNNING HANDLER [app_deploy : restart app container] ****************************************************************************************************
changed: [woolfer-vm]

PLAY RECAP **********************************************************************************************************************************************
woolfer-vm                 : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 

---

### Why roles are idempotent

* Use of `state: present`
* `service: state: started`
* `docker_container: state: started`
* No raw shell commands
* Modules check system state before applying changes

---

## 4. Ansible Vault Usage

**Encrypted file location:**

```
group_vars/all.yml
```

Check encryption:

```bash
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
32626135353732643334383863613364343133653332343963663130383661613264303035633539
6338383862316664333831646339626661333262366564310a613830303165373238393035323531
61303734633766316666343231313765373564313132613862316334303333636366383835326236
3335623233616139310a316132616232376331386661366239376163326665343839626466323636
64353433343361306364363261646534623333376432316164356432376537633036323933643164
37306165626330356632613834363236636530643335393131303364636634383231313665653163
66616462353965333237363461623331613730363734623531626536376136653064306431333236
34646562363534333436313564396561653664386165366163353763396431343766333534306333
34613533666536633862396461663266333834363937373837323162353930666361336135306630
37376463396132306334643535353830653864656266383739636662373632613637323235663165
32613538303632653965386361636530383762396537343164363534323764393062313263383861
39373464396132303062383838336664636635363036363734613166666564313036663761303932
62653839353636363634336434643839373935346333663561663962626339303135316431336163
30363132666537656135343132613736303338303236316239386136616235326631386432313965
33353464343532383739616666363535316430393639333866343961636565303332316530373666
39373864373265656639326164343766383066666135373164636630333038323765303766626339
62336364383362366336393639306530616637626230346665346635383539316163
```

**Vault password management:**

* Stored in `.vault_pass`
* File permissions: `chmod 600`
* Added to `.gitignore`

**Why Vault is important:**

* Prevents committing plain-text secrets
* Protects Docker Hub credentials
* Safe collaboration in Git

---

## 5. Deployment Verification

### Deployment run:

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -b

PLAY [Deploy application] *******************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
ok: [woolfer-vm]

TASK [app_deploy : Login to Docker Hub] *****************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Pull application image] **************************************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Stop existing container if running] **************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Remove old container if exists] ******************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Run application container] ***********************************************************************************************************
changed: [woolfer-vm]

TASK [app_deploy : Wait for application port to be ready] ***********************************************************************************************
ok: [woolfer-vm]

TASK [app_deploy : Verify health endpoint] **************************************************************************************************************
ok: [woolfer-vm]

RUNNING HANDLER [app_deploy : restart app container] ****************************************************************************************************
changed: [woolfer-vm]

PLAY RECAP **********************************************************************************************************************************************
woolfer-vm                 : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ ansible webservers -a "docker ps" -b
[WARNING]: Host 'woolfer-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.19/reference_appendices/interpreter_discovery.html for more information.
woolfer-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                      COMMAND                  CREATED          STATUS          PORTS                    NAMES
6f6255aa815b   woolfer0097kek/devops-info-python:latest   "uvicorn app:app --h…"   32 seconds ago   Up 12 seconds   0.0.0.0:5000->5000/tcp   devops-info-python
woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ curl http://84.252.128.111:5000/health
{"status":"healthy","timestamp":"2026-02-24T21:46:42.338813+00:00","uptime_seconds":26}woolfer0097@woolfer0097-Redmi-Book-Pro-15-2022:~/Code/DevOps-Core-Course1/ansible$ 

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles separate logic into reusable components and improve structure.

**How do roles improve reusability?**
They can be reused across projects and environments with different variables.

**What makes a task idempotent?**
It declares desired state and only changes the system if drift exists.

**How do handlers improve efficiency?**
They run only when notified, preventing unnecessary service restarts.

**Why is Ansible Vault necessary?**
To securely store sensitive data like credentials in version control.

---

## 7. Challenges

* Docker module required `community.docker` collection → installed via ansible-galaxy
* Handler used invalid state → corrected to `restart: true`
* Role path issue → fixed with `roles_path` in ansible.cfg
* Vault variables undefined → fixed by correct path and password loading