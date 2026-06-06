# Jenkins Freestyle: Trello QA + Allure Report + Allure TestOps

Один Freestyle job на агенте **Windows** (как на вашей машине). Репозитории GitHub: `shadow7971247/trello_api`, `trello_ui`, `trello_mobile`.

Порядок прогона: **API → UI → Mobile** (API-first).

---

## 0. Что должно быть на Jenkins-агенте

| Компонент | Зачем |
|-----------|--------|
| **Python 3.12+** | pytest |
| **Git** | checkout |
| **Google Chrome** | UI-тесты (или Selenoid — см. `SELENOID_URL`) |
| **Java 8+** | Allure CLI / плагин Jenkins |
| **allurectl** | загрузка в Allure TestOps |
| **Android SDK + AVD + Appium** | только если гоняете mobile **локально** на этом же агенте |
| **Node/npm** | только если ставите Appium через npm |

Проверка:

```bat
python --version
git --version
allure --version
allurectl --version
```

Установка **allurectl** (один раз на агенте):  
https://docs.qameta.io/allure-testops/ecosystem/allurectl/

---

## 1. Плагины Jenkins

**Manage Jenkins → Plugins → Available:**

1. **Git plugin**
2. **Allure Jenkins Plugin**
3. **Credentials Binding Plugin** (для секретов)
4. *(опционально)* **Environment Injector Plugin** — если удобнее через «Inject environment variables»

После установки Allure: **Manage Jenkins → Tools → Allure Commandline** → Add `Allure` (укажите путь к `allure.bat` или автоустановку).

---

## 2. Allure TestOps (до настройки job)

1. Создайте проект в [Allure TestOps](https://docs.qameta.io/allure-testops/).
2. **Administration → Access Tokens** → API token.
3. Запишите:
   - `ALLURE_ENDPOINT` — URL инстанса, например `https://ваш.testops.cloud`
   - `ALLURE_TOKEN` — токен
   - `ALLURE_PROJECT_ID` — ID проекта (в настройках проекта)

Один **launch** на сборку = объединённые результаты API + UI + Mobile (см. шаг merge ниже).

---

## 3. Credentials в Jenkins

**Manage Jenkins → Credentials → (global) → Add Credentials**

| ID (пример) | Тип | Поля |
|-------------|-----|------|
| `trello-api-secrets` | Username with password **или** Secret text × N | `TRELLO_API_KEY`, `TRELLO_API_TOKEN` |
| `trello-mobile-secrets` *(опционально)* | Username with password | Для mobile: `TRELLO_EMAIL`, `TRELLO_PASSWORD` |
| `allure-testops` | Secret text | `ALLURE_TOKEN` |
| `browserstack` *(опционально)* | Secret text | `BROWSERSTACK_ACCESS_KEY` |

Проще для диплома: один credential **Secret file** `.env` не коммитить — в job создавать `.env` из **Injected secrets** (см. шаг 6).

Минимальный набор переменных:

```env
TRELLO_WEB_URL=https://trello.com
TRELLO_BASE_URL=https://api.trello.com/1
TRELLO_API_KEY=...
TRELLO_API_TOKEN=...
BROWSER=chrome
HEADLESS=true
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
```

Для BrowserStack (отдельный файл `.env.browserstack` или переменные job):

```env
BROWSERSTACK_USERNAME=...
BROWSERSTACK_ACCESS_KEY=...
BROWSERSTACK_APP=bs://...
BROWSERSTACK_BUILD_NAME=%JOB_NAME%-%BUILD_NUMBER%
```

---

## 4. Создание Freestyle job

**New Item →** имя `trello-qa-diploma` → **Freestyle project** → OK.

### 4.1 General

- **Description**: Trello API + UI + Mobile, Allure Report + TestOps  
- **Discard old builds**: держать 10–20 сборок  
- *(опционально)* **This project is parameterized**:
  - `Boolean Parameter` `RUN_MOBILE` = false (включить mobile-стадию)
  - `Choice Parameter` `MOBILE_MODE` = `skip` | `browserstack` | `local`

### 4.2 Restrict where this project can be run

- Пусто — любой агент, **или**
- Label `windows` — UI + API на Windows-агенте  
- Label `android` — только для job с локальным эмулятором

### 4.3 Source Code Management

**Вариант A (рекомендуется): один checkout скриптом** — оставьте **None**, клонирование в первом Build Step.

**Вариант B:** три отдельных Freestyle job (api / ui / mobile) + **Build other projects** downstream.

Ниже — **вариант A**, одна job.

---

## 5. Build Environment

**☑ Provide Configuration files** — не обязательно.

**Inject environment variables** (если есть плагин) или задайте в bat/ps1:

```text
WORKSPACE_ROOT=%WORKSPACE%
TRELLO_API_PATH=%WORKSPACE%\trello_api
ALLURE_RESULTS_ROOT=%WORKSPACE%\allure-results-merged
JOB_LAUNCH_NAME=trello-qa-%JOB_NAME%-%BUILD_NUMBER%
```

**☑ Use secret text(s) or file(s)** — привязать `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `ALLURE_TOKEN` (UI job без email/password).

---

## 6. Build Steps

### Step 1 — Checkout (Execute Windows batch command)

Подставьте URL или SSH (если Jenkins уже с GitHub credentials):

```bat
cd /d "%WORKSPACE%"
if not exist trello_api git clone https://github.com/shadow7971247/trello_api.git trello_api
if not exist trello_ui git clone https://github.com/shadow7971247/trello_ui.git trello_ui
if not exist trello_mobile git clone https://github.com/shadow7971247/trello_mobile.git trello_mobile
cd trello_api && git pull && cd ..
cd trello_ui && git pull && cd ..
cd trello_mobile && git pull && cd ..
```

### Step 2 — Создать `.env` для UI/Mobile (batch)

Секреты подставьте через **Credentials Binding** или вручную для первого прогона:

```bat
cd /d "%WORKSPACE%\trello_ui"
(
echo TRELLO_WEB_URL=https://trello.com
echo TRELLO_BASE_URL=https://api.trello.com/1
echo TRELLO_API_KEY=%TRELLO_API_KEY%
echo TRELLO_API_TOKEN=%TRELLO_API_TOKEN%
echo BROWSER=chrome
echo HEADLESS=true
echo BROWSER_WIDTH=1920
echo BROWSER_HEIGHT=1080
) > .env

copy /Y .env "%WORKSPACE%\trello_mobile\.env"
```

### Step 3 — Python venv + API tests

```bat
cd /d "%WORKSPACE%\trello_api"
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
set TRELLO_BASE_URL=https://api.trello.com/1
pytest -m "not browserstack" --alluredir=allure-results
if errorlevel 1 exit /b 1
call .venv\Scripts\deactivate.bat
```

### Step 4 — UI tests

```bat
cd /d "%WORKSPACE%\trello_ui"
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
set TRELLO_API_PATH=%WORKSPACE%\trello_api
pytest -m "not browserstack" --alluredir=allure-results
if errorlevel 1 exit /b 1
call .venv\Scripts\deactivate.bat
```

### Step 5 — Mobile (опционально)

**BrowserStack** (без эмулятора на агенте):

```bat
cd /d "%WORKSPACE%\trello_mobile"
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
set TRELLO_API_PATH=%WORKSPACE%\trello_api
set MOBILE_RUN_CONTEXT=browserstack
set BROWSERSTACK_BUILD_NAME=%JOB_NAME%-%BUILD_NUMBER%
REM Создайте .env.browserstack из секретов Jenkins (см. .env.browserstack.example в репо)
pytest -m "cloud_smoke" --run-context browserstack --alluredir=allure-results
call .venv\Scripts\deactivate.bat
```

**Локальный эмулятор** (агент с `adb` + Appium):

```bat
adb devices
pytest -m "not browserstack" --run-context local --alluredir=allure-results
```

### Step 6 — Объединить Allure-результаты для отчёта и TestOps

```bat
cd /d "%WORKSPACE%"
if exist allure-results-merged rmdir /s /q allure-results-merged
mkdir allure-results-merged
if exist trello_api\allure-results xcopy /E /I /Y trello_api\allure-results\* allure-results-merged\
if exist trello_ui\allure-results xcopy /E /I /Y trello_ui\allure-results\* allure-results-merged\
if exist trello_mobile\allure-results xcopy /E /I /Y trello_mobile\allure-results\* allure-results-merged\
```

---

## 7. Post-build Actions

### 7.1 Allure Report (в Jenkins UI)

**Post-build Actions → Allure Report**

| Поле | Значение |
|------|----------|
| Path | `allure-results-merged` |
| JDK | (пусто или JDK агента) |
| Report title | `Trello QA #%BUILD_NUMBER%` |

После сборки в job появится вкладка **Allure Report** с графиками и вложениями.

### 7.2 Allure TestOps (upload)

**Post-build Actions → Execute Windows batch command** *(или отдельный шаг «всегда», Even unstable)*:

```bat
cd /d "%WORKSPACE%"
allurectl upload ^
  --endpoint %ALLURE_ENDPOINT% ^
  --token %ALLURE_TOKEN% ^
  --project-id %ALLURE_PROJECT_ID% ^
  --launch-name "%JOB_LAUNCH_NAME%" ^
  allure-results-merged
```

`ALLURE_ENDPOINT`, `ALLURE_PROJECT_ID` — как **Environment variables** job или global properties Jenkins.

Проверка в TestOps: Launches → ваш `trello-qa-...-%BUILD_NUMBER%`.

### 7.3 Артефакты (опционально)

**Archive the artifacts**: `allure-results-merged/**`

---

## 8. Схема сборки

```text
Checkout (3 repo)
    → .env (Trello secrets)
    → trello_api: pytest → allure-results
    → trello_ui:  pytest → allure-results  (TRELLO_API_PATH)
    → trello_mobile: pytest (optional) → allure-results
    → merge → allure-results-merged
Post-build:
    → Allure Report (plugin)
    → allurectl upload → TestOps
```

---

## 9. Три отдельных Freestyle job (альтернатива)

| Job | Команда | Allure launch |
|-----|---------|---------------|
| `trello-api` | `pytest -m smoke` | `trello-api-%BUILD_NUMBER%` |
| `trello-ui` | `pytest -m ui` + `TRELLO_API_PATH` | `trello-ui-%BUILD_NUMBER%` |
| `trello-mobile` | `pytest -m mobile` или `cloud_smoke` | `trello-mobile-%BUILD_NUMBER%` |

В конце — четвёртая job **trello-allure-upload** только с `xcopy` + `allurectl`, триггер **Build other projects** после трёх upstream.

---

## 10. Частые проблемы

| Симптом | Решение |
|---------|---------|
| `Не найден trello_api` | `set TRELLO_API_PATH=%WORKSPACE%\trello_api` перед UI/Mobile |
| Chrome не стартует | `HEADLESS=true`, установить Chrome на агенте |
| Push protection / секреты в логах | не архивировать `pytest_*.txt`, `.env` только из Credentials |
| UI не видит доску | API создаёт `prefs_permissionLevel=public`; проверить `TRELLO_API_KEY` / `TRELLO_API_TOKEN` |
| Mobile local | отдельный агент с AVD; Appium `appium -p 4723` |
| BrowserStack timeout | firewall; `BROWSERSTACK_APP=bs://...`; проверить credentials |
| Пустой Allure Report | путь `allure-results-merged`, шаг merge после pytest |
| TestOps 401 | проверить `ALLURE_TOKEN` и `ALLURE_ENDPOINT` |

---

## 11. Соответствие диплому (qa-guru)

- **Jenkins** — Freestyle job с последовательными стадиями  
- **Allure Report** — плагин + `--alluredir`  
- **Allure TestOps** — `allurectl upload` с launch на сборку  
- **API / UI / Mobile** — три репозитория, API-first  

Маркер для полного локального набора без облака: `-m "not browserstack"`.
