import json

from util import Util
from random import randint
from collections import OrderedDict
from datetime import datetime
import hashlib
from cryptography import KeyGen as keygen
from numba import jit

cryptography = keygen()
util = Util()
global difficulty
difficulty = 1

class Keys:
    genesis_keys = cryptography.generate_keys()
    genesis_alphanumeric_address = genesis_keys[2]
    genesis_private_key = genesis_keys[1]
    genesis_public_key = genesis_keys[0]
class tx:
    def __init__(self, sender_public_key, recipient_public_key, amount, signature, index):
        self.state = 0
        self.own_weight = 1
        self.cumulative_weight = 0 + self.own_weight
        self.previous_hashes = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d, %H:%M:%S.%f EST')
        self.signature = signature
        self.recipient_public_key = recipient_public_key
        self.sender_public_key = sender_public_key
        self.amount = amount
        self.index = index + 1
        self.nonce = Graph.puzzle(Graph, self.previous_hashes, self.signature, self.timestamp)
    def previous(self):
        x = self.__dict__
        x['previous_hashes'] = list(x['previous_hashes'])
        return x
    def hash_data(data):
        data = str(data).encode('utf-8')
        h = hashlib.sha256(data)
        return h.hexdigest()
    def get_hash(self):
        return self.hash_data(self.get_transaction_dict())
    def get_transaction_dict(self):
        transaction_dict = OrderedDict({
            'sender' : self.sender_public_key,
            'recipient' : self.recipient_public_key,
            'amount': self.amount,
            'timestamp' : self.timestamp,
            'own_weight' : self.own_weight,
            'cumulative_weight' : self.cumulative_weight,
            'edges' : self.previous_hashes,
            'index' : self.index,
            'signature' : self.signature,
            'nonce' : self.nonce
        })
        return transaction_dict
class Graph():
    def __init__(self, *args):
        self.graph = OrderedDict()
        self.state = 0

        keys = Keys()
        genesis_address = keys.genesis_alphanumeric_address
        genesis_private_key = keys.genesis_private_key
        genesis_public_key = keys.genesis_public_key

        # You may want to make several thousands on the Mainnet for security from potential high weight attacks.

        gen_tx_one = tx(genesis_address, genesis_address, 0,
                        keygen.sign_tx(genesis_public_key, genesis_private_key, "Genesis"),
                        index=self.count_tx_number())
        self.update_cumulative_weights(gen_tx_one, ["None"])
        gen_tx_key = self.attach_transaction(gen_tx_one, ["None"])

        gen_tx_two = tx(genesis_address, None, 0,
                        keygen.sign_tx(genesis_public_key, genesis_private_key, "Genesis"),
                        index=self.count_tx_number())
        self.update_cumulative_weights(gen_tx_two, [gen_tx_key])
        self.attach_transaction(gen_tx_two, [gen_tx_key])

        gen_tx_three = tx(genesis_address, None, 0,
                          keygen.sign_tx(genesis_public_key, genesis_private_key, "Genesis"),
                          index=self.count_tx_number())
        self.update_cumulative_weights(gen_tx_three, [gen_tx_key])
        self.attach_transaction(gen_tx_three, [gen_tx_key])
    def count_tx_number(self):
        tx_number = 0
        for x in self.graph:
            tx_number += 1
        return tx_number
    def attach_transaction(self, transaction, confirmed_transactions):
        self.pending_transactions = []
        self.failed_transactions = []
        self.pending_transactions.append(transaction)

        is_valid = self.is_valid_transaction(transaction)

        if is_valid == True:
            utils = Util()
            x = utils.str_join([
                transaction.timestamp,
                transaction.sender_public_key,
                transaction.recipient_public_key,
                transaction.amount,
                transaction.previous_hashes,
            ])
            transaction.key = utils.hash(x)
            self.tx_key = transaction.key

            for tx in confirmed_transactions:
                transaction.previous_hashes.append(tx)

            self.graph.update({transaction.key: transaction})

            serializable_format = ({})
            for (k, v) in self.graph.items():
                serializable_format.update({k: v.get_transaction_dict()})
                sort_by = "index"  # Options are: "index", "amount", "own_weight" or "timestamp"
            serializable_format = sorted(serializable_format.items(), key=lambda x: x[1][sort_by], reverse=True)

            with open("graph.json", 'w') as f:
                f.truncate(0)
                json.dump(serializable_format, f)

            self.pending_transactions.remove(transaction)
            self.state += 1
            return self.tx_key

        else:
            if is_valid == False:
                self.failed_transactions.append(transaction)
                raise RuntimeError('[!] Invalid transaction. Attachment failed.')
                return None
            if is_valid == None and util.get_graph_tx_count() > 4:
                raise RuntimeError('[!] Could not determine if the transaction was supposed to be accepted or rejected.')
                pass
            if is_valid == None and util.get_graph_tx_count() <= 4:
                return True
            else:
                raise RuntimeError('[!] This transaction is a unique one...')
    def get_pending_transactions(self):
        return self.pending_transactions
    def get_failed_transactions(self):
        return self.failed_transactions
    def does_address_exist(self, address):
        graph = util.get_graph()
        address_list = []
        for x in graph.values():
            address_list.append(x['sender'])
            address_list.append(x['recipient'])
        if address in address_list:
            return True
        else:
            return False
            raise LookupError('The address you are trying to send cryptocurrency to does not exist')
    def is_valid_transaction(self, transaction):
        return True
    def confirm_transactions(self):
        tip_one, tip_two = self.select_tips()
        self.is_valid_transaction(tip_one)
        self.is_valid_transaction(tip_two)
        return tip_one['key'], tip_two['key']
    def select_tips(self):
        available_transactions = []
        selected_transactions = []

        tip_quantity = 2

        for key in self.graph:
            _transaction = (self.graph[key].__dict__)
            available_transactions.append(_transaction)

        if len(available_transactions) >= 1:
            for i in range(tip_quantity):
                selected_transactions.append(available_transactions[randint(0, len(available_transactions) - 1)])

            if selected_transactions[0] == selected_transactions[1]:
                while selected_transactions[0] == selected_transactions[1]:
                    selected_transactions[1] = available_transactions[randint(0, len(available_transactions) - 1)]
        return selected_transactions[0], selected_transactions[1]
    def valid_proof(self, previous_hashes, signature, timestamp, nonce):
        guess = (str(previous_hashes) + str(signature) + str(timestamp) + str(nonce)).encode('utf-8')
        h = hashlib.new('sha256')
        h.update(guess)
        guess_hash = h.hexdigest()
        return guess_hash[:difficulty] == '0' * difficulty
    def puzzle(self, previous_hashes, signature, timestamp):
        nonce = 0
        while not self.valid_proof(self, previous_hashes, signature, timestamp, nonce):
            nonce = nonce + 1
        return nonce
    def update_cumulative_weights(self, transaction, confirmed_transactions):
        graph = self.graph
        for key in graph:
            if key in confirmed_transactions:
                a = graph[key]
                self_cumulative_weight = transaction.cumulative_weight
                tip_cumulative_weight = a.cumulative_weight
                a.cumulative_weight = self_cumulative_weight + tip_cumulative_weight

    @jit(forceobj=True)
    def make_transaction(self, sender_public_key, recipient_public_key, amount, signature):
        confirmed_transactions = self.confirm_transactions()
        if len(confirmed_transactions) >= 2:
            new_transaction = tx(sender_public_key, recipient_public_key, amount, signature, index=self.count_tx_number())
            self.update_cumulative_weights(new_transaction, confirmed_transactions)
            return self.attach_transaction(new_transaction, confirmed_transactions)