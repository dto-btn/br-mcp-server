import json
import logging
import time
import os

import pyodbc

from business_request.br_utils import _data_serializer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DatabaseConnection:
    """Database connection class."""
    def __init__(self, server, username, password, database, port=None):
        # Handle cases where port is included in the server string (e.g., server.database.windows.net:1433)
        if ":" in server:
            self.server, port_from_server = server.split(":")
            self.port = int(port_from_server)
        else:
            self.server = server
            self.port = int(port) if port else 1433
            
        self.username = username
        self.password = password
        self.database = database
        # Use ODBC Driver 18 as default for modern Azure SQL connections
        self.driver = os.getenv("ODBC_DRIVER", "{ODBC Driver 18 for SQL Server}")

    def get_conn(self):
        """Get the database connection using pyodbc."""
        logger.debug("Requesting connection to %s:%s via %s", self.server, self.port, self.driver)
        
        conn_str = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return pyodbc.connect(conn_str)

    def execute_query(self, query, *args, result_key='br') -> dict:
        """
        Executes a query against the database

        The returned content will always be in JSON format with items as column values
        """
        # Get the database connection
        try:
            conn = self.get_conn()
        except pyodbc.Error as e:
            logger.error("Failed to connect to the database: %s", e)
            raise

        cursor = conn.cursor()

        try:
            logger.debug("About to run this query %s \nWith those params: %s", query, args)
            # Start timing the query execution
            start_time = time.time()

            cursor.execute(query, args)
            rows = cursor.fetchall()

            # End timing the query execution
            end_time = time.time()
            execution_time = end_time - start_time

            # Log the query execution time
            logger.info("Query executed in %s seconds", execution_time)

            # Fetch column names
            columns = [desc[0] for desc in cursor.description]

            # Create a list of lists of dictionaries with one key-value pair each
            #result = [[{columns[i]: row[i]} for i in range(len(columns))] for row in rows] # type: ignore
            result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows] # type: ignore
            logger.debug("Found %s results!", len(result))

            extraction_date = result[0].get("EXTRACTION_DATE") if result else None
            total_count = result[0].get("TotalCount") if result else None

            # Remove both TotalCount and ExtractionDate from the result if they exist
            cleaned_result = [
                {k: v for k, v in item.items() if k not in ["TotalCount", "EXTRACTION_DATE", "BR_ACTIVE_EN", "BR_ACTIVE_FR"]}
                for item in result
            ]

            final_result = {
                result_key: cleaned_result,
                'metadata': {
                    'execution_time': execution_time,
                    'results': len(result),
                    'total_rows': total_count,
                    'extraction_date': extraction_date,
                }
            }

            # Convert the result to JSON
                                                    #needed for the date serialization
            json_result = json.dumps(final_result, default=_data_serializer, indent=4)
            return json.loads(json_result)

        finally:
            # Ensure the connection is closed
            conn.close()