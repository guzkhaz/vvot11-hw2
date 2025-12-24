# ВВОТ: Домашняя работа 2. Генератор конспектов лекций

Инфраструктура предназначена для сервиса, который принимает видеофайлы лекций, расшифровывает их, генерирует и хранит текстовые конспекты.

## Структура проекта
````
├── src/                      
│   ├── web/                       # Веб-приложение
│   │   ├── app.py                 # Главный файл приложения
│   │   ├── routes.py              # Определение маршрутов API
│   │   ├── clients.py             # Клиенты для внешних сервисов
│   │   ├── config.py              # Конфигурация приложения
│   │   ├── database.py            # Работа с базой данных YDB
│   │   ├── requirements.txt      
│   │   ├── Dockerfile             # Контейнеризация веб-приложения
│   │   └── templates/             # Шаблоны веб-интерфейса
│   │       ├──index.html
│   │       └──tasks.html
│   │
│   └── generator/                 # Сервис фоновой обработки
│       ├── app.py                 # Основной файл генератора
│       ├── task_processor.py      # Обработчик задач из очереди
│       ├── ai_services.py         # Интеграция с YandexGPT и SpeechKit
│       ├── media_processing.py    # Обработка медиа
│       ├── document_generation.py # Генерация PDF конспектов
│       ├── storage_utils.py       # Работа с Object Storage
│       ├── cloud_utils.py         # Утилиты для Yandex Cloud
│       ├── file_utils.py          # Работа с файлами
│       ├── ffmpeg                 # Библиотека обработки медиа 
│       ├── Montserrat.ttf         # Шрифт для PDF
│       ├── requirements.txt      
│       └── Dockerfile             # Контейнеризация генератора
│
├── terraform/                    
│   ├── main.tf                 
│   ├── variables.tf            
│   └── outputs.tf                         
│
├── .gitignore                     
└── README.md
````
## Использованные сервисы Yandex Cloud
### Основные сервисы
1. Yandex Serverless Containers	
2. Yandex API Gateway	
3. Yandex YDB (Serverless)	
4. Yandex Object Storage	
5. Yandex Message Queue	
6. Yandex Container Registry
7. Yandex Functions Triggers
### AI-сервисы
1. Yandex SpeechKit
2. YandexGPT API 
### Сервисы безопасности и управления
1. Yandex IAM
2. Yandex Lockbox

## Общая архитектура

Веб-приложение развернуто в **Yandex Cloud** и построено на serverless-архитектуре с асинхронной обработкой заданий.

Пользовательский HTTPS-доступ обеспечивается через **Yandex API Gateway**, который проксирует запросы в **Serverless Container (web)**. Веб-контейнер отображает интерфейс, принимает данные пользователя и создаёт задания на генерацию конспекта.

Все задания сохраняются в **YDB (serverless)** и помещаются в общую очередь **Yandex Message Queue**, за счет чего обеспечивается асинхронная обработка и возможность параллельного выполнения нескольких задач.

Фоновая обработка выполняется отдельным **Serverless Container (generator)**, который запускается автоматически через **Trigger**, подписанный на очередь. Генератор проверяет ссылку Яндекс Диска, загружает видео, преобразует аудио в текст с помощью **Yandex SpeechKit**, формирует конспект с использованием **YandexGPT**, генерирует PDF и сохраняет его в приватный **Object Storage**.

Секреты и ключи доступа хранятся в **Yandex Lockbox** и передаются в контейнеры через переменные окружения. Docker-образы хранятся в **Yandex Container Registry**. Все доступы управляются через **IAM** и сервисный аккаунт.

Вся инфраструктура создаётся и удаляется с помощью Terraform с использованием входных переменных и единого префикса ресурсов.

## Инструкция по развертыванию
### Подготовка переменных окружения
```
export TF_VAR_yc_token=$(yc iam create-token)
export TF_VAR_cloud_id=<cloud_id>
export TF_VAR_folder_id=<folder_id>
export TF_VAR_prefix=hw2-summary
```
### Развертывание инфраструктуры
1) Инициализация Terraform
```
terraform init
```
2) Проверка плана
```
terraform plan 
```
3) Применение конфигурации
```
terraform apply 
```
### Контейнеризация образов
1. Сборка Docker-образов
```
docker build -t cr.yandex/<registry_id>/hw2-web:latest src/web
docker build -t cr.yandex/<registry_id>/hw2-generator:latest src/generator
```
2. Публикация Docker-образов в Container Registry
```
docker push cr.yandex/<registry_id>/hw2-web:latest
docker push cr.yandex/<registry_id>/hw2-generator:latest
```

Ссылка на скринкаст : [Яндекс.Диск]() 

   
