# NHL Screener

Скринер для анализа статистики матчей NHL с расчётом вероятностей тоталов.

## Функционал

- Просмотр расписания матчей на неделю вперёд
- Статистика команд по последним N матчам (по умолчанию 15)
- Разделение статистики на домашние/выездные матчи
- Индивидуальный тотал команды (2+, 3+, 4+, 5+, 6+ шайб)
- Общий тотал матча (5+, 6+, 7+, 8+ голов)
- Взвешенный расчёт вероятности (недавние матчи важнее)
- Раскрывающийся список матчей при клике на статистику

## Установка и запуск

### Backend (Python FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Или используйте `run_backend.bat`

### Frontend (Vue.js)

```bash
cd frontend
npm install
npm run dev
```

Или используйте `run_frontend.bat`

## Первый запуск

1. Запустите backend
2. Запустите frontend
3. Откройте http://localhost:3000
4. Нажмите "Обновить данные" для загрузки команд и матчей из NHL API

## API Endpoints

- `GET /api/teams` - список всех команд
- `GET /api/teams/{abbrev}/stats` - статистика команды
- `GET /api/schedule/upcoming` - расписание на неделю
- `GET /api/match/analysis?home_team=WSH&away_team=CAR` - анализ матча
- `POST /api/sync/teams` - синхронизация команд
- `POST /api/sync/games` - синхронизация матчей
- `GET /api/status` - статус системы

## Технологии

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vue.js 3, Vite, Axios
- **API**: NHL Web API (api-web.nhle.com)
