# import logging
# import json
# import mysql.connector
# from typing import Dict, Any
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage, SystemMessage
# from urllib.parse import urlparse, parse_qs
# import os

# logger = logging.getLogger(__name__)


# class TableAgent:
#     """
#     Agent responsible for generating and executing SQL queries for data processing
#     """

#     def __init__(self, gemini_api_key: str, schema_path: str = None):
#         """
#         Initialize the Table Agent with Gemini LLM and schema path

#         Args:
#             gemini_api_key (str): Google Gemini API key
#             schema_path (str, optional): Path to schema.json file
#         """
#         self.llm = ChatGoogleGenerativeAI(
#             model="gemini-1.5-flash",
#             google_api_key=gemini_api_key,
#             temperature=0.1  # Low temperature for precise SQL generation
#         )
#         # Default schema path if not provided
#         self.schema_path = schema_path or os.path.join(
#             os.path.dirname(__file__), '..', 'utils', 'schema.json'
#         )
#         # Load schema during initialization
#         self.schema = self._load_schema()
#         logger.info("Table Agent initialized successfully")

#     def _load_schema(self) -> Dict[str, Any]:
#         """
#         Load the database schema from schema.json

#         Returns:
#             Dict[str, Any]: Schema data or empty dict on failure
#         """
#         try:
#             with open(self.schema_path, 'r') as f:
#                 schema = json.load(f)
#             logger.debug(
#                 f"Schema loaded from {self.schema_path}: {json.dumps(schema, indent=2)}")
#             print(f"[DEBUG] Schema loaded successfully: {schema}")
#             return schema
#         except Exception as e:
#             logger.error(f"Failed to load schema.json: {e}")
#             return {}

#     def process_query(self, query: str) -> str:
#         """
#         Generate and execute SQL query based on user query

#         Args:
#             query (str): The user query

#         Returns:
#             str: Formatted query result or error message
#         """
#         try:
#             print(f"[DEBUG] Table Agent processing query: {query}")

#             if not self.schema:
#                 logger.error("No schema available for query processing")
#                 return f"Error: Could not load schema for query: {query}"

#             # Generate SQL query
#             sql_query = self._generate_sql_query(query)

#             if "Cannot generate SQL" in sql_query:
#                 logger.warning(
#                     f"LLM could not generate SQL for query: {query}")
#                 return f"Unable to process data query: {query}"

#             # Execute SQL query
#             result = self._execute_sql_query(sql_query, query)
#             return result

#         except Exception as e:
#             logger.error(f"Error in Table Agent: {e}", exc_info=True)
#             return f"Error processing query: {query}"

#     def _generate_sql_query(self, query: str) -> str:
#         """
#         Generate a MySQL SELECT query using the LLM

#         Args:
#             query (str): User query

#         Returns:
#             str: Generated SQL query or error message
#         """
#         system_prompt = """
#         You are an expert SQL query generator. Based on the provided database schema and user query, generate a valid SQL SELECT query for MySQL.
#         - Use only the tables and columns defined in the schema.
#         - Table names may contain spaces or special characters (e.g., "pdf_b55f83da_table_1_25").
#         - Map schema data types to MySQL types: "String" to VARCHAR, "Integer" to INT.
#         - Ensure the query is syntactically correct and optimized for MySQL.
#         - Do not include INSERT, UPDATE, or DELETE statements.
#         - If the query cannot be answered with the schema, return "Cannot generate SQL for this query."
#         - Return only the SQL query, without explanations or additional text.
#         - If aggregations (e.g., COUNT, SUM, AVG) are needed, use them appropriately.
#         - Handle joins if multiple tables are required, using appropriate keys (e.g., product or product_supplied for relationships).

#         Schema:
#         {schema}

#         User Query: {query}
#         """

#         formatted_prompt = system_prompt.format(
#             schema=json.dumps(self.schema, indent=2),
#             query=query
#         )
#         logger.debug(f"Formatted prompt for LLM: {formatted_prompt}")

#         messages = [
#             SystemMessage(content=formatted_prompt),
#             HumanMessage(content=f"Generate SQL for query: {query}")
#         ]

#         try:
#             response = self.llm.invoke(messages)
#             sql_query = response.content.strip()
#             # Remove Markdown code block markers if present
#             if sql_query.startswith('```sql'):
#                 sql_query = sql_query.replace(
#                     '```sql', '').replace('```', '').strip()
#             logger.debug(f"Raw LLM response: {response.content}")
#             print(f"[DEBUG] Raw LLM response: {response.content}")
#             logger.debug(f"Cleaned SQL query: {sql_query}")
#             print(f"[DEBUG] Cleaned SQL query: {sql_query}")
#             return sql_query
#         except Exception as e:
#             logger.error(f"Error generating SQL query: {e}")
#             return f"Cannot generate SQL for this query"

#     def _execute_sql_query(self, sql_query: str, original_query: str) -> str:
#         """
#         Execute the SQL query on the MySQL database

#         Args:
#             sql_query (str): SQL query to execute
#             original_query (str): Original user query for context

#         Returns:
#             str: Formatted query result or error message
#         """
#         try:
#             # Database URL (prefer environment variable)
#             db_url = os.getenv(
#                 'database_url',
#                 'mysql+pymysql://admin:AlphaBeta1212@mydb.ch44qeeiq2ju.ap-south-1.rds.amazonaws.com:3306/My_database?charset=utf8mb4'
#             )

#             # Parse the database URL
#             parsed_url = urlparse(db_url)
#             query_params = parse_qs(parsed_url.query)
#             charset = query_params.get('charset', ['utf8mb4'])[0]
#             database = parsed_url.path.lstrip('/')

#             # Connect to MySQL
#             conn = mysql.connector.connect(
#                 host=parsed_url.hostname,
#                 user=parsed_url.username,
#                 password=parsed_url.password,
#                 database=database,
#                 port=parsed_url.port or 3306,
#                 charset=charset
#             )
#             cursor = conn.cursor()
#             logger.debug(f"Connected to MySQL database: {database}")
#             print(f"[DEBUG] Connected to MySQL database: {database}")

#             # Execute the query
#             cursor.execute(sql_query)
#             results = cursor.fetchall()
#             logger.debug(f"Query executed successfully. Results: {results}")
#             print(f"[DEBUG] Query execution results: {results}")

#             # Format the results
#             if results:
#                 # For a SUM query, expect a single value
#                 if len(results) == 1 and len(results[0]) == 1:
#                     total_quantity = results[0][0]
#                     return f"Total quantity of '{original_query.split('of')[1].strip().strip('?')}' sold: {total_quantity}"
#                 else:
#                     return f"Query results: {results}"
#             else:
#                 logger.warning(f"No results returned for query: {sql_query}")
#                 return f"No results found for query: {original_query}"

#         except mysql.connector.Error as db_err:
#             logger.error(f"MySQL error: {db_err}")
#             return f"Database error while processing query: {original_query}"
#         except Exception as e:
#             logger.error(f"Error executing SQL query: {e}")
#             return f"Error executing query: {original_query}"
#         finally:
#             if 'cursor' in locals():
#                 cursor.close()
#             if 'conn' in locals():
#                 conn.close()
#             logger.debug("MySQL connection closed")

#     def health_check(self) -> Dict[str, Any]:
#         """
#         Perform health check for the Table Agent

#         Returns:
#             Dict[str, Any]: Health status information
#         """
#         try:
#             # Test LLM connection
#             test_response = self.llm.invoke([HumanMessage(content="Hello")])
#             # Check schema availability
#             schema_loaded = bool(self.schema)
#             # Test database connection
#             db_url = os.getenv(
#                 'database_url',
#                 'mysql+pymysql://admin:AlphaBeta1212@mydb.ch44qeeiq2ju.ap-south-1.rds.amazonaws.com:3306/My_database?charset=utf8mb4'
#             )
#             parsed_url = urlparse(db_url)
#             query_params = parse_qs(parsed_url.query)
#             charset = query_params.get('charset', ['utf8mb4'])[0]
#             database = parsed_url.path.lstrip('/')

#             conn = mysql.connector.connect(
#                 host=parsed_url.hostname,
#                 user=parsed_url.username,
#                 password=parsed_url.password,
#                 database=database,
#                 port=parsed_url.port or 3306,
#                 charset=charset
#             )
#             conn.close()

#             return {
#                 "table_agent": True,
#                 "llm_connection": True,
#                 "schema_loaded": schema_loaded,
#                 "db_connection": True,
#                 "overall_health": True
#             }
#         except Exception as e:
#             logger.error(f"Table Agent health check failed: {e}")
#             return {
#                 "table_agent": False,
#                 "llm_connection": False,
#                 "schema_loaded": bool(self.schema),
#                 "db_connection": False,
#                 "overall_health": False,
#                 "error": str(e)
#             }
import logging
import json
import mysql.connector
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from urllib.parse import urlparse, parse_qs
import os

logger = logging.getLogger(__name__)


class TableAgent:
    """
    Agent responsible for generating and executing SQL queries for data processing
    """

    def __init__(self, gemini_api_key: str, schema_path: str = None):
        """
        Initialize the Table Agent with Gemini LLM and schema path

        Args:
            gemini_api_key (str): Google Gemini API key
            schema_path (str, optional): Path to schema.json file
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.1  # Low temperature for precise SQL generation
        )
        # Default schema path if not provided
        self.schema_path = schema_path or os.path.join(
            os.path.dirname(__file__), '..', 'utils', 'schema.json'
        )
        # Load schema during initialization
        self.schema = self._load_schema()
        logger.info("Table Agent initialized successfully")

    def _load_schema(self) -> Dict[str, Any]:
        """
        Load the database schema from schema.json

        Returns:
            Dict[str, Any]: Schema data or empty dict on failure
        """
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            logger.debug(
                f"Schema loaded from {self.schema_path}: {json.dumps(schema, indent=2)}")
            print(f"[DEBUG] Schema loaded successfully: {schema}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema.json: {e}")
            return {}

    def process_query(self, query: str) -> str:
        """
        Generate and execute SQL query based on user query

        Args:
            query (str): The user query

        Returns:
            str: Formatted query result or error message
        """
        try:
            print(f"[DEBUG] Table Agent processing query: {query}")

            if not self.schema:
                logger.error("No schema available for query processing")
                return f"Error: Could not load schema for query: {query}"

            # Generate SQL query
            sql_query = self._generate_sql_query(query)

            if "Cannot generate SQL" in sql_query:
                logger.warning(
                    f"LLM could not generate SQL for query: {query}")
                return f"Unable to process data query: {query}"

            # Execute SQL query
            result = self._execute_sql_query(sql_query, query)
            return result

        except Exception as e:
            logger.error(f"Error in Table Agent: {e}", exc_info=True)
            return f"Error processing query: {query}"

    def _generate_sql_query(self, query: str) -> str:
        """
        Generate a MySQL SELECT query using the LLM, supporting multi-table joins

        Args:
            query (str): User query

        Returns:
            str: Generated SQL query or error message
        """
        system_prompt = """
        You are an expert SQL query generator. Based on the provided database schema and user query, generate a valid SQL SELECT query for MySQL.
        - Use only the tables and columns defined in the schema.
        - Table names may contain spaces or special characters (e.g., "pdf_b55f83da_table_1_25").
        - Map schema data types to MySQL types: "String" to VARCHAR, "Integer" to INT.
        - Ensure the query is syntactically correct and optimized for MySQL.
        - Do not include INSERT, UPDATE, or DELETE statements.
        - If the query cannot be answered with the schema, return "Cannot generate SQL for this query."
        - Return only the SQL query, without explanations or additional text.
        - If aggregations (e.g., COUNT, SUM, AVG) are needed, use them appropriately.
        - For queries requiring data from multiple tables, use appropriate JOINs (INNER JOIN, LEFT JOIN, etc.) based on relationships defined in the schema.
        - Assume tables from the same PDF share common columns (e.g., 'product' or 'product_supplied') for joins, as specified in the schema's relationships.
        - If no explicit relationship exists, infer joins based on common column names (e.g., 'product') across tables.
        - Ensure table aliases are used for clarity in multi-table queries.

        Schema:
        {schema}

        User Query: {query}
        """

        formatted_prompt = system_prompt.format(
            schema=json.dumps(self.schema, indent=2),
            query=query
        )
        logger.debug(f"Formatted prompt for LLM: {formatted_prompt}")

        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=f"Generate SQL for query: {query}")
        ]

        try:
            response = self.llm.invoke(messages)
            sql_query = response.content.strip()
            # Remove Markdown code block markers if present
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace(
                    '```sql', '').replace('```', '').strip()
            logger.debug(f"Raw LLM response: {response.content}")
            print(f"[DEBUG] Raw LLM response: {response.content}")
            logger.debug(f"Cleaned SQL query: {sql_query}")
            print(f"[DEBUG] Cleaned SQL query: {sql_query}")
            return sql_query
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return f"Cannot generate SQL for this query"

    def _execute_sql_query(self, sql_query: str, original_query: str) -> str:
        """
        Execute the SQL query on the MySQL database

        Args:
            sql_query (str): SQL query to execute
            original_query (str): Original user query for context

        Returns:
            str: Formatted query result or error message
        """
        try:
            # Database URL (prefer environment variable)
            db_url = os.getenv(
                'database_url',
                'mysql+pymysql://admin:AlphaBeta1212@mydb.ch44qeeiq2ju.ap-south-1.rds.amazonaws.com:3306/My_database?charset=utf8mb4'
            )

            # Parse the database URL
            parsed_url = urlparse(db_url)
            query_params = parse_qs(parsed_url.query)
            charset = query_params.get('charset', ['utf8mb4'])[0]
            database = parsed_url.path.lstrip('/')

            # Connect to MySQL
            conn = mysql.connector.connect(
                host=parsed_url.hostname,
                user=parsed_url.username,
                password=parsed_url.password,
                database=database,
                port=parsed_url.port or 3306,
                charset=charset
            )
            cursor = conn.cursor()
            logger.debug(f"Connected to MySQL database: {database}")
            print(f"[DEBUG] Connected to MySQL database: {database}")

            # Execute the query
            cursor.execute(sql_query)
            results = cursor.fetchall()
            logger.debug(f"Query executed successfully. Results: {results}")
            print(f"[DEBUG] Query execution results: {results}")

            # Get column names for better result formatting
            columns = [desc[0] for desc in cursor.description]
            logger.debug(f"Column names: {columns}")

            # Format the results
            if results:
                # For a SUM query, expect a single value
                if len(results) == 1 and len(columns) == 1:
                    total_quantity = results[0][0]
                    return f"Total quantity of '{original_query.split('of')[1].strip().strip('?')}' sold: {total_quantity}"
                else:
                    # Format multi-column results
                    formatted_results = [dict(zip(columns, row))
                                         for row in results]
                    return f"Query results: {json.dumps(formatted_results, indent=2)}"
            else:
                logger.warning(f"No results returned for query: {sql_query}")
                return f"No results found for query: {original_query}"

        except mysql.connector.Error as db_err:
            logger.error(f"MySQL error: {db_err}")
            return f"Database error while processing query: {original_query}"
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return f"Error executing query: {original_query}"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            logger.debug("MySQL connection closed")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the Table Agent

        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            # Test LLM connection
            test_response = self.llm.invoke([HumanMessage(content="Hello")])
            # Check schema availability
            schema_loaded = bool(self.schema)
            # Test database connection
            db_url = os.getenv(
                'database_url',
                'mysql+pymysql://admin:AlphaBeta1212@mydb.ch44qeeiq2ju.ap-south-1.rds.amazonaws.com:3306/My_database?charset=utf8mb4'
            )
            parsed_url = urlparse(db_url)
            query_params = parse_qs(parsed_url.query)
            charset = query_params.get('charset', ['utf8mb4'])[0]
            database = parsed_url.path.lstrip('/')

            conn = mysql.connector.connect(
                host=parsed_url.hostname,
                user=parsed_url.username,
                password=parsed_url.password,
                database=database,
                port=parsed_url.port or 3306,
                charset=charset
            )
            conn.close()

            return {
                "table_agent": True,
                "llm_connection": True,
                "schema_loaded": schema_loaded,
                "db_connection": True,
                "overall_health": True
            }
        except Exception as e:
            logger.error(f"Table Agent health check failed: {e}")
            return {
                "table_agent": False,
                "llm_connection": False,
                "schema_loaded": bool(self.schema),
                "db_connection": False,
                "overall_health": False,
                "error": str(e)
            }
