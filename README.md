📝 Personal Blog API
Asinxron arxitekturaga asoslangan, yuqori tezlikda ishlovchi blog platformasi backend REST API loyihasi.

Loyihada maqolalar (posts), ierarxik izohlar (nested comments), teglash tizimi, reaksiyalar (likes) hamda JWT orqali xavfsiz autentifikatsiya to'liq amalga oshirilgan.

⚡ Asosiy Imkoniyatlar
Foydalanuvchilar & Xavfsizlik: Ro'yxatdan o'tish, login, JWT tokenlar (Access & Refresh) rotatsiyasi va parollarni xavfsiz heshlash.

Maqolalar (Posts): CRUD operatsiyalari, avtomatik unikal slug generatsiyasi, qidiruv (search), teglarga ko'ra filtrlash va paginatsiya.

Daraxtsimon Izohlar (Nested Comments): Cheksiz darajali javob (reply) qaytarish imkoniyatiga ega izohlar tizimi.

Interaktivlik: Maqolalarga like bosish/qaytarib olish (toggle) va ko'rishlar sonini avtomatik hisoblash.

Optimallashgan So'rovlar: Asinxron SQLAlchemy 2.0 yordamida N+1 muammosisiz (joinedload, selectinload) tuzilgan SQL so'rovlar.

🛠 Texnologiyalar
Framework: FastAPI

ORM: SQLAlchemy 2.0 (Async) + Alembic

Ma'lumotlar bazasi: PostgreSQL 16

Kesh / Sessiyalar: Redis 7

Drayver: asyncpg

Muhit & Konteyner: Docker & Docker Compose, uv

🚀 Ishga Tushirish
Repozitoriyadan nusxa oling va .env faylini sozlang:

Bash
cp .env.example .env
Docker Compose orqali barcha servislarni ishga tushiring:

Bash
docker compose up --build -d
Migratsiyalarni bazaga qo'llang:

Bash
docker compose exec app alembic upgrade head
API hujjati (Swagger UI): http://localhost:8000/docs manzilida mavjud.
