import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
import argparse
from resources.sql import SQLConnection
from resources.helper_functions import load_aml_env_variables


# Get latest dataset from SQL database
def dataprep(sql_conn, query):
    # Turn SQL data into csv file
    df = pd.read_sql(query, sql_conn.sql_conn)
    df.drop(['file_name'], axis=1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', dest='output_path', required=True)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df), args.output_path)

    print(f"Wrote test to {args.output_path} and train to {args.output_path}")


if __name__ == '__main__':
    env_variables = load_aml_env_variables()

    input_sql_conn = SQLConnection(env_variables.get('sql_server'), env_variables.get('sql_database'),
                                   env_variables.get('sql_username'), env_variables.get('sql_password'))
    # TODO: Add name of SQL table
    input_query = "SELECT * FROM ExampleTable"

    with input_sql_conn:
        dataprep(input_sql_conn, input_query)
