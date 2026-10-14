from databricks import sql


connection = sql.connect(
    server_hostname="dbc-43e699c4-9a50.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/94e1603badec3227",
    auth_type="databricks-cli",
    profile="dbc-43e699c4-9a50"
)

cursor = connection.cursor()

cursor.execute("""
    SELECT
        COUNT(*) AS total_records
    FROM workspace.default.data_quality_results
""")

result = cursor.fetchone()

print("Total quality records:", result[0])

cursor.close()
connection.close()