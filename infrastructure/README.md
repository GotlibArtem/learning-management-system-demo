# Demo infra

## Usage

This is an an [Ansible playbook](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html). One should install ansible, download required roles and launch the play:

```bash
$ python -m venv venv
$ . venv/bin/activate
$ make install
$
$ ansible-playbook -i hosts site.yml -b
```

## Highlights
* Variables in `vars/secrets.yml` are encrypted. Key should be stored at `.vault-key`. To obtain the key, contact fedor@borshev.com
* Developer accounts are stored in 02_accounts.yml
* Security configuration is based on [geerlingguy.security](https://github.com/geerlingguy/ansible-role-security). Customisations are stored in `roles/common/meta.yml`.


## Development
To run the linters use:

```bash
$ . venv/bin/activate
$ make lint
```


