import os
import datetime
import subprocess
from flask import Flask, request
from google.cloud import storage
from google.cloud import secretmanager


def get_db_password(secret_name, project_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def upload_to_gcs(local_path, bucket_name, gcs_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)


def dump_database(request):
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    region = os.environ["REGION"]
    db_instance_name = os.environ["DB_INSTANCE_NAME"]
    db_name = os.environ["DB_NAME"]
    db_user = os.environ["DB_USER"]
    secret_name = os.environ["SECRET_NAME"]
    gcs_bucket = os.environ["GCS_BUCKET"]

    instance_connection_name = f"{project_id}:{region}:{db_instance_name}"

    password = get_db_password(secret_name, project_id)
    dump_base_name = os.environ.get("DUMP_BASE_NAME", f"{db_instance_name}_{db_name}")
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M")
    filename = f"{dump_base_name}_{timestamp}.dump"
    filepath = f"/tmp/{filename}"

    excluded_schemas = os.environ.get("EXCLUDED_SCHEMAS", "")
    exclude_schema_args = []
    if excluded_schemas:
        for schema in excluded_schemas.split(","):
            schema = schema.strip()
            if schema:
                exclude_schema_args.extend(["--exclude-schema", schema])

    excluded_tables = os.environ.get("EXCLUDED_TABLES", "")
    exclude_table_args = []
    if excluded_tables:
        for table in excluded_tables.split(","):
            table = table.strip()
            if table:
                exclude_table_args.extend(["--exclude-table", table])

    included_schemas = os.environ.get("INCLUDED_SCHEMAS", "")
    include_schema_args = []
    if included_schemas:
        for schema in included_schemas.split(","):
            schema = schema.strip()
            if schema:
                include_schema_args.extend(["--schema", schema])

    included_tables = os.environ.get("INCLUDED_TABLES", "")
    include_table_args = []
    if included_tables:
        for table in included_tables.split(","):
            table = table.strip()
            if table:
                include_table_args.extend(["--table", table])

    dump_cmd = [
        "pg_dump",
        f"--host=/cloudsql/{instance_connection_name}",
        "--username",
        db_user,
        "--format=custom",
        "--file",
        filepath,
        *include_schema_args,
        *include_table_args,
        *exclude_schema_args,
        *exclude_table_args,
        db_name,
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    try:
        subprocess.run(dump_cmd, check=True, env=env)
        upload_to_gcs(filepath, gcs_bucket, filename)
        return f"Dump uploaded to gs://{gcs_bucket}/{filename}", 200
    except subprocess.CalledProcessError as e:
        return f"pg_dump failed: {e}", 500
    except Exception as e:
        return f"Error: {e}", 500


app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def run_dump():
    return dump_database(request)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
