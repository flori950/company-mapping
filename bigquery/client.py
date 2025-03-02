import pandas as pd
import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPIError
from google.oauth2.service_account import Credentials
from helpers.decorators import retry
from logger import Logger as logger


class BigQueryClient():
    """ BigQuery client. """
    max_retries = 5
    retry_delay = 10

    def __init__(self, project_id, dataset_name):
        """
        Initialize the BigQueryClient.

        Args:
            project_id (str): The project id.
            dataset_name (str): The dataset name.
        """
        self.project_id = project_id
        self.dataset_name = dataset_name
        self.dataset_refstring = "{}.{}".format(self.project_id, self.dataset_name)
        self.dataset = None
        self.expiration_time = 1000 * 60 * 60 * 24 * 30
        self.max_retries = 5
        self.sleep_amount = 10

        try:
            private_key = os.getenv('GOOGLE_PRIVATE_KEY')
            private_key = private_key.replace("\\n", "\n")
            # Create the credentials dictionary
            credentials_dict = {
                "type": os.getenv('GOOGLE_TYPE'),
                "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
                "private_key": private_key,
                "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL'),
                "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
            }

            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            self.client = bigquery.Client(credentials=credentials)
            logger.success("BigQuery credentials initialised.")
        except DefaultCredentialsError as e:
            logger.error(f"Problem with BigQuery credentials: {e}")
            exit(1)

    @retry(max_retries, retry_delay)
    def dataset_exists(self) -> bool:
        """
        Check if the dataset exists in BigQuery.

        Returns:
            bool: True if dataset exists, False otherwise.
        """
        try:
            self.dataset = self.client.get_dataset(self.dataset_refstring)
            logger.info("Dataset exsist in BigQuery")
            return True
        except NotFound:
            logger.info("Dataset doesn't exsist in BigQuery")
            return False

    @retry(max_retries, retry_delay)
    def create_dataset(self):
        """ Create a dataset in BigQuery. """
        try:
            self.dataset = self.client.create_dataset(self.dataset_name, timeout=30)
            self.dataset.location = "europe-west3"
            self.dataset.default_table_expiration_ms = self.expiration_time
        except GoogleAPIError as e:
            logger.error(f"Google API Error (create_dataset): {e}")

    @retry(max_retries, retry_delay)
    def get_dataset(self) -> bigquery.Dataset:
        """
        Get a dataset from BigQuery.

        Returns:
            bigquery.Dataset: The dataset.
        """
        try:
            bq_dataset = self.client.get_dataset(self.dataset_refstring)
            return bq_dataset
        except GoogleAPIError as e:
            logger.error(f"Google API Error (get_dataset): {e}")

    @retry(max_retries, retry_delay)
    def delete_dataset(self):
        """ Delete a dataset in BigQuery."""
        try:
            self.client.delete_dataset(
                self.dataset_refstring, delete_contents=True, not_found_ok=True
            )
        except GoogleAPIError as e:
            logger.error(f"Google API Error (delete_dataset): {e}")

    def table_exists(self, table_name) -> bool:
        """
        Check if a table exists in BigQuery.

        Args:
            table_name (str): The name of the table.

        Returns:
            bool: True if table exists, False otherwise.
        """
        try:
            table_id = "{}.{}".format(self.dataset_refstring, table_name)
            self.client.get_table(table_id)
            return True
        except NotFound:
            return False

    @retry(max_retries, retry_delay)
    def create_table(self, table_name, schema) -> bigquery.Table:
        """
        Create a table in BigQuery.

        Args:
            table_name (str): The name of the table.
            schema (list): The schema of the table.

        Returns:
            bigquery.Table: The created table.
        """
        try:
            table_id = "{}.{}".format(self.dataset_refstring, table_name)
            table = bigquery.Table(table_id, schema=schema)
            # add field for partitioning
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.HOUR,
                field="dwh_partitiondate",
                expiration_ms=self.expiration_time,
            )
            bq_table = self.client.create_table(table)
            return bq_table
        except GoogleAPIError as e:
            logger.error(f"Google API Error (create_table): {e}")

    @retry(max_retries, retry_delay)
    def get_table(self, table_name) -> bigquery.Table:
        """
        Get a table from BigQuery.

        Args:
            table_name (str): The name of the table.

        Returns:
            bigquery.Table: The table.
        """
        try:
            table_id = "{}.{}".format(self.dataset_refstring, table_name)
            bq_table = self.client.get_table(table_id)
            return bq_table
        except GoogleAPIError as e:
            logger.error(f"Google API Error (get_table): {e}")

    @retry(max_retries, retry_delay)
    def load_table_from_dataframe(self, dataframe, table_name, job_config) -> bigquery.LoadJob:
        """
        Load a dataframe into a table in BigQuery.

        Args:
            dataframe (pandas.DataFrame): The dataframe to load.
            table_name (str): The name of the table.
            job_config (bigquery.LoadJobConfig): The job configuration.

        Returns:
            bigquery.LoadJob: The load job.
        """
        try:
            table_id = "{}.{}".format(self.dataset_refstring, table_name)
            job = self.client.load_table_from_dataframe(
                dataframe,
                table_id,
                job_config=job_config
            )
            return job
        except GoogleAPIError as e:
            logger.error(f"Google API Error (load_table_from_dataframe): {e}")

    @retry(max_retries, retry_delay)
    def delete_table(self, table_name):
        """
        Delete a table in BigQuery.

        Args:
            table_name (str): The name of the table.
        """
        try:
            table_id = "{}.{}".format(self.dataset_refstring, table_name)
            self.client.delete_table(table_id, not_found_ok=True)
        except GoogleAPIError as e:
            logger.error(f"Google API Error (delete_table): {e}")

    @retry(max_retries, retry_delay)
    def create_view(self, query, view_name):
        """
        Create a view in BigQuery.

        Args:
            query (str): The query to execute.
            view_name (str): The name of the view.
        """
        try:
            view_id = "{}.{}".format(self.dataset_refstring, view_name)
            view = bigquery.Table(view_id)
            view.view_query = query
            view = self.client.create_table(view)
        except GoogleAPIError as e:
            logger.error(f"View could not created: {e}")

    def update_view(self, query, view_name):
        """
        Update a view in BigQuery. That means Drop and create the view.

        Args:
            query (str): The query to execute.
            view_name (str): The name of the view.
        """
        try:
            view_id = "{}.{}".format(self.dataset_refstring, view_name)
            self.client.delete_table(view_id, not_found_ok=True)
            self.create_view(query, view_name)
        except GoogleAPIError as e:
            logger.error(f"Google API Error (update_view): {e}")

    @retry(max_retries, retry_delay)
    def execute_query(self, query) -> bigquery.QueryJob:
        """
        Execute a query in BigQuery.

        Args:
            query (str): The query to execute.

        Returns:
            bigquery.QueryJob: The query job.
        """
        try:
            query_job = self.client.query(query)
            return query_job
        except GoogleAPIError as e:
            logger.error(f"Google API Error (execute_query): {e}")

    @retry(max_retries, retry_delay)
    def get_dataframe(self, query):
        """
        Get a dataframe from a query.

        Args:
            query (str): The query to execute.

        Returns:
            pandas.DataFrame: The dataframe.
        """
        try:
            logger.debug("Query")
            logger.debug(query)
            query_job = self.client.query(query)
            query_job.result()
            return query_job.to_dataframe()
        except GoogleAPIError as e:
            logger.error(f"Google API Error (get_dataframe): {e}")

    @retry(max_retries, retry_delay)
    def check_is_no_duplicate(self, tablename, dataframe):
        """
        Check if the dataframe is a duplicate.

        Args:
            tablename (str): The name of the table.
            dataframe (pandas.DataFrame): The dataframe.

        Returns:
            bool: True if duplicate, False otherwise.
        """
        try:
            if dataframe.empty:
                logger.info("Dataframe is empty")
                return True
            datetobefiltered = dataframe['dwh_partitiondate'].iloc[0]
            # Reformat the timestamp to a valid DATETIME format
            formatted_datetime = pd.to_datetime(datetobefiltered, "%Y-%m-%d %H:%M:%S.%f")
            result = self.get_dataframe(
                """
                Select dwh_partitiondate FROM {}
                WHERE dwh_partitiondate = DATETIME("{}")
                LIMIT 1
                """.format(tablename, formatted_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            )
            logger.debug("result")
            logger.debug(result)
            logger.debug("result.__len__()")
            logger.debug(result.__len__())
            if result is not None and result.__len__() == 0:
                logger.info("No duplicate detected")
                return True
            else:
                logger.error("Warning: there was a duplicate detected.")
                return False
        except GoogleAPIError as e:
            logger.error(f"Google API Error (check_is_no_duplicate): {e}")
