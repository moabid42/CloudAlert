import os
import json
import pandas
from neo4j import GraphDatabase
from IPython.display import Markdown
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = "bolt://localhost:7687"
NEO4J_QUERIES_FILE = 'queries.json'

class NeoDB():
    def __init__(self):
        # Obtain Neo4j connection string from environment variables
        self._parse_env_vars()
        # Instantiate the Neo4j python driver
        self._driver = GraphDatabase.driver(NEO4J_URI,
                                            auth=(self._neo4j_user, self._neo4j_password))
        print('Init done!')

    def _parse_env_vars(self):
        self._neo4j_user = os.environ['NEO4J_USER']
        self._neo4j_password = os.environ['NEO4J_PASSWORD']

    @staticmethod
    def _exec_query(tx, query, kwargs):
        if kwargs:
            result = tx.run(query, **kwargs)
        else:
            result = tx.run(query)
        return result

    def query(self, q, kwargs):
        with self._driver.session() as session:
            return session.read_transaction(self._exec_query, q, kwargs)

    def close(self):
        self._driver.close()


class QueryBuilder():
    def __init__(self):
        # Initialize DB
        self.db = NeoDB()
        # Load the queries file into memory
        with open(NEO4J_QUERIES_FILE, 'r') as fp:
            body = fp.read()
            self.QUERIES = json.loads(body)
        print('QueryBuilder is initilized correctly')

    @staticmethod
    def _n_recent_days(N):
        return (datetime.utcnow() - timedelta(days=N))

    @staticmethod
    def printmd(string):
        display(Markdown(string))

    def _print_index(self, queries):
        num_queries = len(queries)
        self.printmd("### Queries included in this report")
        text = "| # | Name | Description |\n|---|---|---|"
        for counter, q in enumerate(queries, 1):
            href = self._print_header(q, counter, num_queries).replace(" ", "-")
            text = '''{}\n|[{}/{}]|<a href="#{}">{}</a>|{}|'''.format(text,
                                                                      counter, num_queries,
                                                                      href,
                                                                      q['name'],
                                                                      q['description'])
        self.printmd(text)

    @staticmethod
    def _print_header(q, counter, total):
        return "[{}/{}][{}] {}".format(counter, total,
                                       q['name'], q['description'])

    def _parse_dynamic_params(self, q):
        params = q.get('params', '')
        kwargs = ""
        if params:
            # Iterate through the parameters and verify if one matches the supported types
            for p in params.keys():
                kwargs = {}
                # The query has a parameter specifying to
                # retrieve the assets for the N most recent days
                if p == "n_recent_days":
                    kwargs[params[p]["param_name"]] = \
                        str(self._n_recent_days(params[p]["param_value"]))
        return kwargs

    def _filter_by_tags(self, queries, tags):
        # Returns all the queries which contain all the tags provided
        return [q for q in queries if all(elem in q['tags'] for elem in tags)]

    def _filter_by_account(self, cypher, account):
        if account:
            if 'WHERE' in cypher:
                cypher = cypher.replace(' WHERE ', ' WHERE a.name = "{}" and '.format(account))
            else:
                cypher = cypher.replace(' RETURN ', ' WHERE a.name = "{}" RETURN '.format(account))
        return cypher

    def _run_queries(self, queries, account):
        num_queries = len(queries)
        # For each selected query
        for counter, q in enumerate(queries, 1):
            self.printmd("--- \n## {}".format(self._print_header(q, counter, num_queries)))
            self.printmd("[Goto Top](#Queries-included-in-this-report)")
            # Parse optional dynamic parameters
            kwargs = self._parse_dynamic_params(q)
            # If an account is provided, inject a WHERE clause to filter by account
            cypher = self._filter_by_account(q['query'], account)
            # Execute the query and get a tabular output
            cypher = "{} {}".format(cypher, q['return'])
            res = list(self.db.query(cypher, kwargs))
            # Print result
            if res:
                df = pandas.DataFrame(res, columns=q['result_headers'])
                pandas.set_option('display.max_rows', 500)
                pandas.set_option('display.max_colwidth', 0)
                display(df)  # noqa: F821
            else:
                self.printmd("_No Results Found!_")

    def query(self, tags, account=None):
        # Filter queries
        selected_queries = self._filter_by_tags(self.QUERIES, tags)
        # List index of queries that will be run
        self._print_index(selected_queries)
        # Run queries
        self._run_queries(selected_queries, account)


class ReportBuilder():
    def __init__(self):
        self.qb = QueryBuilder()


    def report_aws_security(self, account=None):
        acc = " [{}]".format(account) if account else ""
        self.qb.printmd("# AWS Security Report {}".format(acc))
        self.qb.query(['aws', 'security'], account=account)

    def report_aws_inventory(self, account=None):
        acc = " [{}]".format(account) if account else ""
        self.qb.printmd("# AWS Inventory Report {}".format(acc))
        self.qb.query(['aws', 'inventory'], account=account)

    def report_aws_networking(self, account=None):
        acc = " [{}]".format(account) if account else ""
        self.qb.printmd("# AWS Networking Report {}".format(acc))
        self.qb.query(['aws', 'networking'], account=account)

# if __name__ == '__main__':
#     QueryBuilder()