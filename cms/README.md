# CMS — Ansible-деплой Nginx + PostgreSQL + FastAPI

Плейбук разворачивает приложение из [`docker-compose-template/`](../docker-compose-template/)
на сервере `ai.hse.akhcheck.ru`: Nginx (reverse-proxy) + FastAPI + PostgreSQL,
всё через Docker Compose, идемпотентно.

Внешний URL после деплоя: `http://ai.hse.akhcheck.ru:20092` (для логина `ai2026-hse-092`,
порт = `20000 + user_id`).

## Структура

```
cms/
├── ansible.cfg
├── inventory.ini              # хост ai.hse.akhcheck.ru
├── playbook.yml               # плейбук
├── requirements.yml           # ansible-galaxy collections
├── group_vars/
│   └── all.yml                # переменные + inline-зашифрованный пароль БД
├── templates/
│   ├── .env.j2                # HOST_PORT, COMPOSE_PROJECT_NAME, POSTGRES_PASSWORD
│   └── db.env.j2              # POSTGRES_PASSWORD для контейнера postgres
├── gitlab-ci.deploy-stage.example.yml
└── README.md
```

## Подготовка (один раз)

1. Установить Ansible и коллекции:
   ```bash
   pip install ansible
   ansible-galaxy collection install -r cms/requirements.yml
   ```
2. (Опционально, рекомендую) положить SSH-ключ на сервер, чтобы не вводить пароль каждый раз:
   ```bash
   ssh-copy-id ai2026-hse-092@ai.hse.akhcheck.ru
   ```
   Если оставляешь логин по паролю — поставь `sshpass` (`brew install hudochenkov/sshpass/sshpass` на macOS).

## Запуск

Пароль Vault — **`secret`** (зашит в условии задания, проверяющий запускает с `--ask-vault-pass`).

```bash
cd cms
ansible-playbook -i inventory.ini playbook.yml --ask-vault-pass --ask-pass
# Vault password: secret
# SSH password:   <пароль от ai2026-hse-092>
```

После успешного выполнения открой `http://ai.hse.akhcheck.ru:20092`.

Если уже настроен SSH-ключ — флаг `--ask-pass` не нужен.

## Идемпотентность

Повторный запуск того же плейбука **не меняет ни одной задачи** (все статусы `ok`):

- модули `apt`, `file`, `get_url`, `template`, `git` — нативно идемпотентны;
- блок установки Docker запускается только если `docker --version` или
  `docker compose version` отсутствуют;
- `community.docker.docker_compose_v2` со `state: present` поднимает контейнеры
  только если конфигурация изменилась.

## Секреты (Ansible Vault)

Пароль БД лежит в [`group_vars/all.yml`](group_vars/all.yml) как inline-vault
(`!vault |`). YAML-структура читаема — зашифровано только значение.

Перешифровать (например, для смены пароля БД):
```bash
ansible-vault encrypt_string --ask-vault-pass --name 'postgres_password' 'НОВЫЙ_ПАРОЛЬ'
# Vault password: secret  (обязательно secret!)
```
И заменить блок `postgres_password: !vault | ...` в `group_vars/all.yml`.

## Встраивание в Delivery (GitLab CI)

См. пример [`gitlab-ci.deploy-stage.example.yml`](gitlab-ci.deploy-stage.example.yml).
В переменных проекта GitLab нужно завести:
- `VAULT_PASSWORD` (значение `secret`) — тип File или Variable
- `SSH_PRIVATE_KEY` — приватный ключ для `ai2026-hse-092`
- `SSH_USER` — `ai2026-hse-092`

## Если на сервере нет Docker и нет sudo

Свяжись с курсом — поставить Docker должен админ сервера. Плейбук определит
отсутствие Docker и попытается поставить с `become: true`, но без sudo задача
упадёт. На shared-сервере курса Docker, как правило, уже стоит.
