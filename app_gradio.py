#!/usr/bin/env python3
"""
🔮 Human Design Calculator — Gradio UI + REST API
Запуск: python app_gradio.py
UI: http://localhost:7860
API: POST /api/calculate
Docs: http://localhost:7860/docs
"""

import gradio as gr
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from chart import calculate_chart
import uvicorn
import json

# ============================================================================
# 🔹 ГРАДИО ИНТЕРФЕЙС
# ============================================================================

def translate_center(center: str) -> str:
    """Перевод названий центров на русский"""
    return {
        'Head': 'Голова', 'Ajna': 'Аджна', 'Throat': 'Горло',
        'Self': 'G-центр', 'Heart': 'Эго', 'Sacral': 'Сакрал',
        'Solar Plexus': 'Эмоциональный', 'Spleen': 'Селезёнка', 'Root': 'Корень'
    }.get(center, center)

def translate_type(hd_type: str) -> str:
    return {
        'Generator': 'Генератор',
        'Manifesting Generator': 'Манифестирующий Генератор',
        'Projector': 'Проектор',
        'Manifestor': 'Манифестор',
        'Reflector': 'Рефлектор'
    }.get(hd_type, hd_type)

def translate_authority(auth: str) -> str:
    return {
        'Emotional': 'Эмоциональный',
        'Sacral': 'Сакральный',
        'Splenic': 'Селезёночный',
        'Ego': 'Эго',
        'Self-Projected': 'Самовыражение',
        'Mental/Outer': 'Ментальный/Внешний'
    }.get(auth, auth)

def calculate_hd(year, month, day, hour, minute, city):
    """Обработчик формы Gradio"""
    try:
        result = calculate_chart(
            birth_year=int(year),
            birth_month=int(month),
            birth_day=int(day),
            birth_hour=int(hour),
            birth_minute=int(minute),
            utc_offset=None  # геокодинг внутри calculate_chart
        )
        
        summary = f"""### 🎯 Результат
| Параметр | Значение |
|----------|----------|
| **Тип** | {translate_type(result['type'])} |
| **Профиль** | {result['profile']} |
| **Авторитет** | {translate_authority(result['authority'])} |

**Определённые центры**: {', '.join(translate_center(c) for c in result['defined_centers'])}

**Активные ворота**: {result['all_active_gates']}

📍 *Город*: {city} | *UTC offset*: {result.get('location_metadata', {}).get('calculated_offset', 'N/A')}"""
        
        return summary, result
        
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", None

# ============================================================================
# 🔹 FASTAPI + CORS
# ============================================================================

app = FastAPI(
    title="HD Engine API",
    description="Human Design chart calculator with Swiss Ephemeris accuracy",
    version="1.0.0"
)

# CORS для Neocities и других доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://ejo.neocities.org", "https://*.neocities.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель запроса для API
class BirthData(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="Год рождения")
    month: int = Field(..., ge=1, le=12, description="Месяц рождения")
    day: int = Field(..., ge=1, le=31, description="День рождения")
    hour: int = Field(..., ge=0, le=23, description="Час рождения (24h формат)")
    minute: int = Field(..., ge=0, le=59, description="Минуты рождения")
    city: str = Field(..., min_length=2, description="Город, Страна (например: Moscow, Russia)")

@app.post("/api/calculate", summary="Рассчитать карту Дизайна Человека")
async def api_calculate(data: BirthData, request: Request):
    """
    REST API эндпоинт для интеграции с фронтендом.
    
    Возвращает JSON с типом, профилем, авторитетом, центрами и воротами.
    """
    try:
        result = calculate_chart(
            birth_year=data.year,
            birth_month=data.month,
            birth_day=data.day,
            birth_hour=data.hour,
            birth_minute=data.minute,
            utc_offset=None  # геокодинг внутри calculate_chart
        )
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/health", summary="Проверка здоровья API")
async def health_check():
    """Простой health check для мониторинга"""
    return JSONResponse(content={
        "status": "ok",
        "service": "hd-engine",
        "version": "1.0.0"
    })

@app.get("/", summary="Root redirect")
async def root():
    """Перенаправление на Gradio UI"""
    return JSONResponse(content={
        "message": "HD Engine API",
        "ui": "/ui",
        "docs": "/docs",
        "api_calculate": "POST /api/calculate"
    })

# ============================================================================
# 🔹 МОНТИРУЕМ GRADIO ПОД /ui
# ============================================================================

with gr.Blocks(
    title="🔮 HD Calculator",
    theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="blue"),
    css="""
        footer {visibility: hidden}
        .gradio-container {max-width: 900px !important}
    """
) as demo:
    gr.Markdown("## 🔮 Калькулятор Дизайна Человека")
    gr.Markdown("На основе [human-design-py](https://github.com/ayfio/human-design-py) • Лицензия: MIT")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Данные рождения")
            year = gr.Number(label="📅 Год", value=1990, precision=0, minimum=1900, maximum=2100)
            month = gr.Number(label="🗓️ Месяц", value=1, precision=0, minimum=1, maximum=12)
            day = gr.Number(label="📆 День", value=1, precision=0, minimum=1, maximum=31)
            hour = gr.Number(label="🕐 Час (24h)", value=12, precision=0, minimum=0, maximum=23)
            minute = gr.Number(label="⏱️ Минуты", value=0, precision=0, minimum=0, maximum=59)
            city = gr.Textbox(
                label="📍 Город, Страна",
                value="Moscow, Russia",
                placeholder="e.g. Moscow, Russia",
                info="Укажите страну для точного геокодинга"
            )
            submit_btn = gr.Button("🔮 Рассчитать карту", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Результат")
            output_markdown = gr.Markdown(label="📋 Результат", value="*Заполните форму и нажмите «Рассчитать»*")
            with gr.Accordion("📦 Raw JSON", open=False):
                output_json = gr.JSON(label="Raw JSON")
    
    # Примеры для быстрого теста
    gr.Examples(
        examples=[
            [1990, 5, 13, 4, 3, "Moscow, Russia"],
            [1985, 12, 25, 18, 30, "New York, USA"],
            [2000, 1, 1, 0, 0, "London, UK"],
            [1995, 8, 20, 14, 15, "Tokyo, Japan"],
        ],
        inputs=[year, month, day, hour, minute, city],
        outputs=[output_markdown, output_json],
        fn=calculate_hd,
        cache_examples=False
    )
    
    # Логика кнопки
    submit_btn.click(
        fn=calculate_hd,
        inputs=[year, month, day, hour, minute, city],
        outputs=[output_markdown, output_json]
    )
    
    gr.Markdown("---")
    gr.Markdown("""
    **API для разработчиков**:
    - `POST /api/calculate` — рассчитать карту
    - `GET /api/health` — проверка здоровья
    - `GET /docs` — интерактивная документация Swagger
    """)

# Монтируем Gradio под /ui
app = gr.mount_gradio_app(app, demo, path="/ui")

# ============================================================================
# 🔹 ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info",
        access_log=True
    )
