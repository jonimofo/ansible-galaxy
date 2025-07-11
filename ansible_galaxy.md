# Ansible-Galaxy steps

## Initialize Your Ansible Collection
Create the basic directory structure for your collection
```bash
ansible-galaxy collection init jonimofo.infastructure
```

This command creates a directory structure like this:
```bash
jonimofo/
└── infastructure/
    ├── docs/
    ├── galaxy.yml
    ├── plugins/
    ├── roles/
    └── README.md
```

Navigate into your new collection directory:
```bash
cd jonimofo/infastructure
```

## Create the ssh Role
Now, create the ssh role within your collection.
```bash
ansible-galaxy role init roles/ssh
```
This will generate the standard role directory structure inside the roles directory.

## Refine the galaxy.yml and meta/runtime Metadata
- cf example [galaxy.yml](./galaxy.yml)
- cf example [meta/runtime/yml](./meta/runtime.yml) (only version is necessary)

## Initialize the Github repo
```bash
git init
git add .
git commit -m "Initial commit of my_collection"
git branch -M main
git remote add origin https://github.com/my_namespace/my_collection.git
git push -u origin main
```

## Publish to Ansible Galaxy
Build your collection:
```bash
ansible-galaxy collection build
```

This will create a .tar.gz archive in your collection's root directory (e.g., jonimofo-infrastructure-1.0.0.tar.gz).
```bash
ansible-galaxy collection publish jonimofo-infrastructure-1.0.0.tar.gz --api-key YOUR_API_KEY
```

## Use a role in a project
In `requirements.yml`
```yaml
collections:
  - name: jonimofo.infrastructure
    version: "1.0.1"
```

Install the role
```bash
ansible-galaxy collection install -r requirements.yml --force
```

Verify
```bash
ansible-galaxy collection list | grep jonimofo.infrastructure

jonimofo.infrastructure                  1.0.0
```


## In case of updates
Bump the version in your collection’s `galaxy.yml`
```yaml
version: 1.0.1    # ← increment this
```

Commit & push to GitHub
```yaml
git add galaxy.yml README.md
git commit -m "chore: bump to v1.0.1 and update docs"
git tag v1.0.1
# Will push both the main branch update and the new v1.0.1 tag in one go.
git push --follow-tags
```

Rebuild the Collection: Now that you've added the required file, you must rebuild your collection archive.
```bash
ansible-galaxy collection build
```
This will generate a new .tar.gz file with an updated version number (e.g., jonimofo-infrastructure-1.0.1.tar.gz).

Publish to Galaxy
```bash
ansible-galaxy collection publish jonimofo-infrastructure-1.0.1.tar.gz --api-key $ANSIBLE_GALAXY_API_KEY
```
