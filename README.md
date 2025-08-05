# pgdump-function

## Description

This Flask application is designed to run as a Google Cloud Run service. It performs a PostgreSQL database dump and uploads the resulting file to a Google Cloud Storage (GCS) bucket. Database credentials are securely retrieved from Google Secret Manager. The service is typically triggered by a Google Cloud Scheduler job, enabling automated and scheduled backups.

For a detailed explanation and deployment guide, see the blog post: [Automated PostgreSQL Backups with Cloud Run & Scheduler](https://damdevops.com/databases/105/).

## How it works

- **Trigger:** The service exposes a single HTTP endpoint (`/`). When it receives a GET or POST request, it starts the dump process.
- **Secrets:** The database password is fetched from Google Secret Manager using the secret name and project ID provided via environment variables.
- **Dump:** The application constructs a `pg_dump` command using environment variables to include or exclude specific schemas and tables.
- **Upload:** Once the dump is complete, the file is uploaded to the specified GCS bucket. The filename includes a timestamp for easy identification.
- **Response:** The service returns a success message with the GCS path or an error message if the dump/upload fails.

## Environment Variables

Required:
- `GOOGLE_CLOUD_PROJECT`: Google Cloud project ID.
- `REGION`: Cloud SQL instance region.
- `DB_INSTANCE_NAME`: Cloud SQL instance name.
- `DB_NAME`: Database name.
- `DB_USER`: Database user.
- `SECRET_NAME`: Name of the secret in Secret Manager containing the DB password.
- `GCS_BUCKET`: Target GCS bucket for the dump file.

Optional:
- `DUMP_BASE_NAME`: Prefix for the dump file name.
- `EXCLUDED_SCHEMAS`: Comma-separated list of schemas to exclude.
- `EXCLUDED_TABLES`: Comma-separated list of tables to exclude.
- `INCLUDED_SCHEMAS`: Comma-separated list of schemas to include.
- `INCLUDED_TABLES`: Comma-separated list of tables