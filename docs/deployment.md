# Deployment

The public app uses [Netlify](https://steam-discovery.netlify.app/) for the React frontend, [FastAPI Cloud](https://steam-discovery-api.fastapicloud.dev/docs) for the API, and one Supabase PostgreSQL/pgvector database. Existing deployments use free plans with bounded resources and may experience cold starts or service limits.

- **Frontend:** root `netlify.toml` builds `frontend/`, publishes `frontend/dist`, and configures SPA routing. `VITE_API_BASE_URL` is the public API origin; it is embedded in the frontend build and must not contain a secret.
- **Backend:** FastAPI Cloud uses `backend/` as the application directory and the entry point in `backend/pyproject.toml`. Configure the restricted `DATABASE_URL`, exact `ALLOWED_ORIGINS`, and optional Groq settings on the server. Keep migration credentials out of the serving environment.
- **Catalog:** deploy a compatible API and semantic artifact before activating a new catalog. Dashboard analytics and discovery must use the same active generation. See the [catalog workflow](catalog.md).
- **AI:** Groq is optional and rate-limited. Core discovery remains available without it. Never publish provider keys or place them in frontend variables.

The connected production services deploy from the repository's main branch. Confirm each provider's actual deployment status and revision after publishing; a Git push alone does not prove deployment success. Migrations and catalog activation are deliberate developer operations, never API startup side effects. Do not assume free-service limits are permanent.
