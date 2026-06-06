# CI: Jenkins + Allure TestOps

План пайплайна для экосистемы Trello QA.

## Стадии Jenkins (рекомендуемый порядок)

```text
Checkout → API tests → UI tests → Mobile (BrowserStack) → Upload Allure
```

| Stage | Каталог | Команда |
|-------|---------|---------|
| API | `trello_api` | `pytest -m smoke --alluredir=allure-results` |
| UI | `trello_ui` | `pytest -m ui --alluredir=allure-results` |
| Mobile (local) | `trello_mobile` | `pytest -m mobile --run-context local --alluredir=allure-results` |
| Mobile (BS) | `trello_mobile` | `pytest -m cloud_smoke --run-context browserstack --alluredir=allure-results` |

Секреты Jenkins:

- `TRELLO_API_KEY`, `TRELLO_API_TOKEN` (достаточно для API и UI — публичные доски без логина в браузере)
- `TRELLO_EMAIL`, `TRELLO_PASSWORD` — только для **mobile** (вход в приложение)
- BrowserStack: `BROWSERSTACK_USERNAME`, `BROWSERSTACK_ACCESS_KEY`, `BROWSERSTACK_APP` (`bs://...`)
- Allure TestOps: `ALLURE_ENDPOINT`, `ALLURE_TOKEN`, `ALLURE_PROJECT_ID`

Для BrowserStack в job:

- `BROWSERSTACK_BUILD_NAME` = `${JOB_NAME}-${BUILD_NUMBER}`
- `pytest --run-context browserstack` или `MOBILE_RUN_CONTEXT=browserstack`

## Allure TestOps

```bash
allurectl upload --endpoint %ALLURE_ENDPOINT% ^
  --token %ALLURE_TOKEN% ^
  --project-id %ALLURE_PROJECT_ID% ^
  --launch-name "trello-%BUILD_NUMBER%" ^
  allure-results
```

Локально:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Пример Jenkinsfile (черновик)

```groovy
pipeline {
    agent any
    environment {
        MOBILE_RUN_CONTEXT = 'browserstack'
        BROWSERSTACK_BUILD_NAME = "${JOB_NAME}-${BUILD_NUMBER}"
    }
    stages {
        stage('API') {
            steps {
                dir('trello_api') {
                    sh 'pip install -r requirements.txt && pytest -m smoke --alluredir=../allure-results-api'
                }
            }
        }
        stage('UI') {
            steps {
                dir('trello_ui') {
                    sh 'pip install -r requirements.txt && pytest -m ui --alluredir=../allure-results-ui'
                }
            }
        }
        stage('Mobile BrowserStack') {
            steps {
                dir('trello_mobile') {
                    sh 'pip install -r requirements.txt && pytest -m cloud_smoke --run-context browserstack --alluredir=../allure-results-mobile'
                }
            }
        }
    }
}
```

На Windows-агенте замените `sh` на `bat` / PowerShell.

## Mobile на локальном эмуляторе

| Компонент | Назначение |
|-----------|------------|
| Android SDK + AVD | эмулятор (API 30–33) |
| APK Trello | `adb install trello.apk` |
| Appium 2 | `appium -p 4723` |

```bash
pytest -m mobile --run-context local --alluredir=allure-results
```

Учётные данные Trello/API — в `trello_ui/.env`. Параметры эмулятора — в `.env.local`.

**Jenkins:** mobile-стадия на агенте с AVD (`label android-local`), перед прогоном `adb devices`. Секреты: `TRELLO_*` и API.

## BrowserStack (CI mobile)

1. Загрузить APK в App Automate → `BROWSERSTACK_APP=bs://...`
2. `pytest -m cloud_smoke --run-context browserstack`

Подробности: [trello_mobile/README.md](../trello_mobile/README.md).
