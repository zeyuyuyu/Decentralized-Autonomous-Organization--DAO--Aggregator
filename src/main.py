import os
import json
import requests
from typing import List, Dict

class DAOAggregator:
    def __init__(self):
        self.dao_data: List[Dict] = []

    def fetch_dao_data(self):
        """Fetch data from various DAO platforms and aggregate into a single list."""
        # Fetch data from Snapshot
        snapshot_data = self._fetch_snapshot_data()
        self.dao_data.extend(snapshot_data)

        # Fetch data from Gnosis Safe
        gnosis_data = self._fetch_gnosis_data()
        self.dao_data.extend(gnosis_data)

        # Fetch data from other DAO platforms as needed

    def _fetch_snapshot_data(self) -> List[Dict]:
        """Fetch DAO data from the Snapshot platform."""
        snapshot_url = "https://hub.snapshot.org/graphql"
        query = """
        query {
          daos {
            id
            name
            symbol
            network
            strategies {
              name
              params
            }
          }
        }
        """
        response = requests.post(snapshot_url, json={"query": query})
        data = response.json().get("data\