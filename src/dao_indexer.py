import requests
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

class ChainIndexer(ABC):
    @abstractmethod
    def get_daos(self) -> List[Dict]:
        pass

class AragonIndexer(ChainIndexer):
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        
    def get_daos(self) -> List[Dict]:
        # Query Aragon subgraph
        query = '''
        {
          daos(first: 1000) {
            id
            name
            token {
              name
              symbol
              totalSupply
            }
            members {
              id
            }
          }
        }'''
        
        response = requests.post(
            'https://api.thegraph.com/subgraphs/name/aragon/aragon-mainnet',
            json={'query': query}
        )
        return response.json()['data']['daos']

class CompoundIndexer(ChainIndexer):
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    def get_daos(self) -> List[Dict]:
        # Query Compound governance
        query = '''
        {
          governances(first: 1000) {
            id
            proposals {
              id
              description
              state
            }
            delegates {
              id
              votes
            }
          }
        }'''

        response = requests.post(
            'https://api.thegraph.com/subgraphs/name/compound-finance/governance', 
            json={'query': query}
        )
        return response.json()['data']['governances']

class DAOIndexer:
    def __init__(self):
        self.indexers: List[ChainIndexer] = []

    def add_indexer(self, indexer: ChainIndexer) -> None:
        self.indexers.append(indexer)

    def index_all(self) -> Dict[str, List[Dict]]:
        results = {}
        for indexer in self.indexers:
            try:
                daos = indexer.get_daos()
                results[indexer.__class__.__name__] = daos
            except Exception as e:
                print(f'Error indexing {indexer.__class__.__name__}: {str(e)}')
                results[indexer.__class__.__name__] = []
        return results

    def get_dao_count(self) -> int:
        total = 0
        for indexer in self.indexers:
            try:
                total += len(indexer.get_daos())
            except:
                continue
        return total

# Usage example:
'''
indexer = DAOIndexer()
indexer.add_indexer(AragonIndexer('ETH_RPC_URL'))
indexer.add_indexer(CompoundIndexer('ETH_RPC_URL'))

results = indexer.index_all()
print(f'Total DAOs indexed: {indexer.get_dao_count()}')
'''