import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from web3 import AsyncWeb3, WebSocketProvider
from web3.middleware import ExtraDataToPOAMiddleware
from web3.utils.address import to_checksum_address
from eth_utils import keccak, is_address

from event_listener.models import TransferEvent


def format_address(raw_address):
    if isinstance(raw_address, bytes):
        return '0x' + raw_address[-20:].hex()
    return None


class Command(BaseCommand):
    help = "Listens for BAYC transfer events on the Ethereum blockchain."

    def handle(self, *args, **kwargs):
        asyncio.run(self.listen_to_transfer_events())

    def save_transfer_event(self, token_id, from_address, to_address, tx_hash, block_number):
        try:
            transfer_event = TransferEvent(
                token_id=token_id,
                from_address=from_address,
                to_address=to_address,
                tx_hash=tx_hash,
                block_number=block_number,
            )
            transfer_event.save()
            self.stdout.write(f"Recorded transfer: Token ID {token_id} from {from_address} to {to_address}.")
        except Exception as err:
            self.stdout.write(f"Error occurred when saving transfer object: {err}")

    async def listen_to_transfer_events(self):
        backoff = 1 

        while True:
            try:
                w3 = AsyncWeb3(WebSocketProvider(settings.INFURA_WS_URL))

                await w3.provider.connect()
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

                contract_address = to_checksum_address(settings.BAYC_CONTRACT_ADDRESS)
                minimal_abi = self.get_minimal_abi()
                contract = w3.eth.contract(address=contract_address, abi=minimal_abi)
                transfer_event_topic = self.calculate_transfer_event_topic()

                self.stdout.write(f"Transfer event topic: {transfer_event_topic}")

                # process old transactions for testing.
                await self.fetch_and_process_past_logs(w3, contract_address, transfer_event_topic)

                self.stdout.write("Listening for new transfer events...")
                subscription_id = await w3.eth.subscribe("logs", {
                    "address": contract_address,
                    "topics": [transfer_event_topic],
                })

                # Process new events
                await self.process_new_events(w3)

            except Exception as e:
                self.stderr.write(f"Error: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.5, 30)

    def get_minimal_abi(self):
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": True, "name": "tokenId", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            }
        ]

    def calculate_transfer_event_topic(self):
        """Calculate the transfer event topic."""
        transfer_event_topic = keccak(text="Transfer(address,address,uint256)").hex()
        if not transfer_event_topic.startswith("0x"):
            transfer_event_topic = "0x" + transfer_event_topic
        return transfer_event_topic

    async def fetch_and_process_past_logs(self, w3, contract_address, transfer_event_topic):
        """
        need a way to test model validation since i can't get a regular websocket message
        """
        current_block = await w3.eth.get_block('latest')
        estimated_block_24_hours_ago = self.get_estimated_block_24_hours_ago(current_block)

        # Fetch past logs
        past_filter_params = {
            "address": contract_address,
            "topics": [transfer_event_topic],
            "fromBlock": hex(estimated_block_24_hours_ago),  # Convert to hex
            "toBlock": 'latest'
        }

        past_events = await w3.eth.get_logs(past_filter_params)
        self.stdout.write(f"Found {len(past_events)} transfer events in the last 24 hours.")

        for result in past_events:
            await self.process_transfer_event(result)

    def get_estimated_block_24_hours_ago(self, current_block):
        """Estimate the block number from 24 hours ago."""
        block_time = current_block['timestamp']
        time_24_hours_ago = block_time - (24 * 60 * 60)
        estimated_block_24_hours_ago = current_block['number'] - ((block_time - time_24_hours_ago) // 15)
        return estimated_block_24_hours_ago

    async def process_transfer_event(self, result):
        """Process a transfer event."""
        from_address = format_address(result['topics'][1])
        to_address = format_address(result['topics'][2])
        token_id = int(result['topics'][3].hex(), 16)
        tx_hash = result["transactionHash"].hex()
        if not tx_hash.startswith('0x'):
            tx_hash = f"0x{tx_hash}"

        self.stdout.write(f">>>> result: {result['transactionHash'].hex()}; from_address: {from_address}; to_address: {to_address}; token_id: {token_id}")

        # save
        await sync_to_async(self.save_transfer_event)(token_id, from_address, to_address, tx_hash, result["blockNumber"])

    async def process_new_events(self, w3):
        """Process new events as they come in."""
        async for payload in w3.socket.process_subscriptions():
            result = payload["result"]
            if result:
                await self.process_transfer_event(result)
