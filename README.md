# ROLE
You are a senior Python backend developer. Write clean, production-ready code without placeholders or TODOs.
You should carry out the project within this folder; the most important thing is that every installed library must be the latest version. A ready-to-use environment has been set up for you using "uv," and you must follow the specified file structure!!!

# PROJECT
Build a personal blog platform backend REST API.
Stack: FastAPI + SQLAlchemy (async) + PostgreSQL + Redis + Docker.

# FOLDER STRUCTURE
Create exactly this structure:

blog_api/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py        # pydantic-settings, reads .env
│   │   ├── security.py      # bcrypt password hash, JWT create/decode
│   │   └── dependencies.py  # get_session, get_current_user
│   ├── db/
│   │   ├── base.py          # DeclarativeBase
│   │   └── session.py       # async engine + sessionmaker
│   ├── models/
│   │   ├── user.py
│   │   ├── post.py          # includes post_tags association table
│   │   ├── comment.py       # supports nested replies via parent_id
│   │   ├── tag.py
│   │   └── like.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── tag.py
│   ├── repositories/
│   │   ├── post_repo.py
│   │   └── comment_repo.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── post_service.py
│   │   └── comment_service.py
│   └── api/
│       └── v1/
│           ├── router.py
│           ├── auth.py
│           ├── posts.py
│           ├── comments.py
│           ├── tags.py
│           └── users.py
├── alembic/
│   └── versions/
├── alembic.ini
├── .env.example
├── docker-compose.yml
└── requirements.txt

# MODELS
User: id, username(unique), email(unique), hashed_pw, is_active, created_at
  → relationships: posts, comments, likes (all cascade delete-orphan)

Post: id, title, slug(unique, indexed), content(Text), excerpt, is_published(default False),
      views(default 0), user_id(FK→users), created_at, updated_at
  → relationships: author, comments, tags(M2M via post_tags), likes

Comment: id, text, user_id(FK), post_id(FK), parent_id(FK→comments, nullable)
         created_at
  → relationships: author, post, replies, parent (self-referential)

Tag: id, name(unique), slug(unique, indexed)
  → relationship: posts (M2M)

Like: id, user_id(FK), post_id(FK)
  → unique constraint on (user_id, post_id)

# SCHEMAS (Pydantic v2)
PostCreate: title, content, excerpt(optional), is_published(default False), tag_ids(list[int])
PostUpdate: all fields optional (PATCH semantics)
PostList: id, title, slug, excerpt, is_published, views, author(id+username),
          tags(list), like_count, created_at
PostDetail: extends PostList + content + comment_count

UserRegister: username, email, password
TokenOut: access_token, refresh_token, token_type="bearer"

# REPOSITORIES
PostRepository (async):
- get_by_slug(slug) → joinedload(author) + selectinload(tags) +
  selectinload(comments → author, replies → author)
- get_list(tag_slug, author_id, search, page, per_page) →
  joinedload(author) + selectinload(tags) +
  optional outerjoin(tags) for tag filter +
  ilike search on title|content +
  count subquery for total +
  order_by created_at desc + offset/limit
- create(post) → add + commit + refresh
- delete(post) → delete + commit

# SERVICES
PostService:
- create_post: auto-generate slug from title (python-slugify),
  append user_id if slug exists, fetch Tag objects by tag_ids, create Post
- update_post: check ownership (403 if not owner), partial update,
  re-slug if title changed, update tags if tag_ids provided
- toggle_like: if Like exists → delete (return liked:false),
  else create (return liked:true)

AuthService:
- register: check email/username uniqueness, hash password, create User
- login: verify password, return create_tokens(user_id)
- refresh: decode refresh token, return new access token

# API ENDPOINTS
POST   /api/v1/auth/register        → UserOut
POST   /api/v1/auth/login           → TokenOut
POST   /api/v1/auth/refresh         → {access_token}

GET    /api/v1/posts/               → {items, total, page, pages}
       query params: tag(str), search(str), page(int=1), per_page(int=10,max=50)
POST   /api/v1/posts/               → PostDetail [auth required]
GET    /api/v1/posts/{slug}         → PostDetail + increment views
PATCH  /api/v1/posts/{slug}         → PostDetail [auth, owner only]
DELETE /api/v1/posts/{slug}         → 204 [auth, owner only]
POST   /api/v1/posts/{id}/like      → {liked: bool} [auth]

GET    /api/v1/posts/{id}/comments  → list[CommentOut] (nested replies included)
POST   /api/v1/posts/{id}/comments  → CommentOut [auth]
       body: {text, parent_id(optional)}
PATCH  /api/v1/comments/{id}        → CommentOut [auth, owner only]
DELETE /api/v1/comments/{id}        → 204 [auth, owner only]

GET    /api/v1/tags/                → list[TagOut]
POST   /api/v1/tags/                → TagOut [auth]

GET    /api/v1/users/{username}     → UserOut + post_count
PATCH  /api/v1/users/me             → UserOut [auth]

# SECURITY
- Passwords: bcrypt via passlib
- JWT: python-jose, access token TTL=30min, refresh token TTL=7days
- Token payload: {sub: user_id, type: "access"|"refresh"}
- OAuth2PasswordBearer scheme on /api/v1/auth/login
- get_current_user dependency: decode → get User → check is_active

# DATABASE
- Async engine: asyncpg driver  (postgresql+asyncpg://...)
- Session: AsyncSession, expire_on_commit=False
- All FK constraints include ondelete="CASCADE"
- Indexes: slug fields, email, username
- Alembic: configure env.py for async, generate initial migration

# DOCKER
docker-compose.yml must include:
  app:     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  db:      postgres:16-alpine, port 5432, volume for data
  redis:   redis:7-alpine, port 6379

.env.example:
  DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/blog_db
  SECRET_KEY=your-secret-key-here
  REDIS_HOST=redis
  REDIS_PORT=6379
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  REFRESH_TOKEN_EXPIRE_DAYS=7

# REQUIREMENTS
fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg
alembic pydantic-settings python-jose[cryptography]
passlib[bcrypt] python-slugify redis

# RULES
1. Every file must be complete — no "# add logic here" comments
2. Use Mapped[] and mapped_column() syntax (SQLAlchemy 2.0)
3. All DB calls must be async/await
4. Repository handles only DB queries, Service handles business logic
5. Raise HTTPException with proper status codes (401, 403, 404, 409)
6. main.py: include all routers under /api/v1 prefix, add lifespan for DB
7. Generate all files in one pass, do not wait for confirmation