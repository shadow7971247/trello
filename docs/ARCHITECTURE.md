# Архитектура решения

Модель слоёв — **Business Actions → Low Level Actions → Page/Screen/API client** (Semenchenko & Kontyava, COMAQA).  
Схема CI (Jenkins, Selenoid, BrowserStack) описана отдельно в [CI.md](CI.md).

## Экосистема репозиториев

```mermaid
flowchart LR
  subgraph data [Data layer]
    API[trello_api]
  end
  subgraph checks [Verification layer]
    UI[trello_ui read-only web]
    MOB[trello_mobile Appium]
  end
  API -->|публичные доски URL| UI
  API -->|board/card ids deep link| MOB
  API --> Trello[(Trello REST API)]
  UI --> TrelloWeb[Trello Web]
  MOB --> TrelloApp[Trello Android]
```

| Репозиторий | Роль | Паттерн |
|-------------|------|---------|
| **trello_api** | CRUD, auth, провижининг данных | API-клиент по сущностям |
| **trello_ui** | Read-only веб без логина | Page Object |
| **trello_mobile** | E2E в приложении | Screen Object |

---

## Правило 3A (Arrange — Act — Assert)

| Фаза | Где реализовано | Пример |
|------|-----------------|--------|
| **Arrange** | Фикстуры с `yield`, `prepare_*` | `public_test_board`, `created_board` |
| **Act** | Вызов client / page / screen | `api_client.create_board()`, `BoardPage().open_by_url()` |
| **Assert** | Тест или `should_*` / `assert_equals` | `assert_status_code(response, 404)`, `should_have_board_title()` |

Проверки статус-кода и полей ответа **не** спрятаны внутри HTTP-слоя — они в тестах и клиентах через `assert_status_code` / `assert_equals`.

---

## API — trello_api

```mermaid
flowchart TB
  subgraph test [Test pytest + Allure]
    T[test_*.py]
  end
  subgraph business [Business Actions]
    S[Allure steps]
  end
  subgraph low [Low Level Actions]
    C[TrelloApiClient facade]
    CL[clients: boards lists cards ...]
  end
  subgraph po [API layer]
    H[http.py]
    V[validators Pydantic]
    E[endpoints.py]
  end
  subgraph engine [HTTP engine]
    R[requests]
  end
  subgraph global [Global]
    PY[pytest]
    AL[Allure]
  end
  T --> S --> C --> CL --> H --> R
  CL --> V
  CL --> E
  T --> PY
  T --> AL
  F[fixtures/factories Arrange] --> T
```

| Папка / модуль | Слой | Назначение |
|----------------|------|------------|
| `tests/` | Test | Сценарии, маркеры, Assert |
| `fixtures/factories.py` | Arrange | `prepare_board`, `prepare_public_board` |
| `fixtures/generators.py` | Arrange | Имена сущностей |
| `api/client.py` | Low Level | Фасад над клиентами |
| `clients/*` | Low Level | HTTP по сущности + проверка статуса |
| `api/http.py` | Engine | Запрос без auto-raise на 4xx |
| `api/validators.py` | PO | Pydantic-контракты |
| `models/` | PO | Request/response модели |
| `conftest.py` | Arrange | `app_config`, `api_client`, yield-фикстуры |

---

## UI — trello_ui

```mermaid
flowchart TB
  subgraph test [Test]
    T[test_public_*.py]
  end
  subgraph business [Business Actions]
    AS[Allure step открыть доску]
  end
  subgraph low [Low Level Actions]
    BP[BoardPage CardPage methods]
  end
  subgraph po [Page Object]
    LOC[locators elements]
  end
  subgraph engine [UI Engine]
    SE[Selene Selenium]
    BR[browser fixture conftest]
  end
  T --> AS --> BP --> LOC --> SE --> BR
  FIX[public_test_board Arrange] --> T
  API[trello_api prepare_public_board] --> FIX
```

| Модуль | Назначение |
|--------|------------|
| `conftest.py` | Браузер, `api_client`, `public_test_board` (yield) |
| `pages/board_page.py`, `card_page.py` | Page Object |
| `ui_utils/screenshot.py` | `capture_step()` — скриншоты вне page |
| `config.py` | `UiConfig`, одна переменная `SELENOID_URL` |

---

## Mobile — trello_mobile

```mermaid
flowchart TB
  subgraph test [Test]
    T[test_*_mobile.py]
  end
  subgraph low [Low Level Actions]
    SC[LoginScreen WorkspaceScreen BoardScreen CardScreen]
  end
  subgraph engine [Mobile Engine]
    AP[Appium UiAutomator2]
  end
  T --> SC --> AP
  FIX[api_test_board Arrange] --> T
  API[trello_api] --> FIX
```

| Маркер | Где | Тестов |
|--------|-----|--------|
| `cloud_smoke` | Jenkins / BrowserStack | 3 |
| `local_only` | Локальный эмулятор | 7 |

---

## Global entities

| Компонент | Реализация |
|-----------|------------|
| Test Runner | pytest |
| Reporting | Allure Report + Allure TestOps #592 |
| Logging | `utils/logger.py` (API), browser log (UI) |
| CI orchestration | Jenkins job `shadow7971247_trello_v2` |

---

## Ссылки

- [Обзорный README](../README.md)
- [CI и Jenkins](CI.md)
- [Ручные кейсы](MANUAL_TESTS.md)
- Модель слоёв: доклад *«Архитектура решений автоматизации тестирования на уровне диаграмм»* (Semenchenko & Kontyava, COMAQA)
