# bayclistener

## Overview

The Ethereum Transfer Event Listener is a Django application that listens for ERC-721 transfer events (specifically for the Bored Ape Yacht Club - BAYC) on the Ethereum blockchain. It utilizes the Web3.py library for interacting with the Ethereum network.

## Features

- Listens for ERC-721 Transfer events on the Ethereum blockchain.
- Saves transfer event data to a Django model.
- Fetches past events from the last 24 hours upon startup.
- Supports asynchronous operations for efficient event handling.

## Installation

1. Clone the repository:
   ```bash
   git clone hhttps://github.com/robnanola/bayclistener.git
   cd bayclistener
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Django project:
   ```bash
   cd bayclistener
   python manage.py migrate
   ```

5. Update your `settings.py` with your Infura WebSocket URL and BAYC contract address:
   ```python
   INFURA_WS_URL = 'wss://mainnet.infura.io/ws/v3/YOUR_INFURA_PROJECT_ID'
   BAYC_CONTRACT_ADDRESS = '0x1234567890abcdef1234567890abcdef12345678'  # Replace with actual contract address
   ```

## Usage

To start the event listener, run the following command:

```bash
python manage.py listen_transfer_events
```


To start the django local server to view the transaction endpoint, run the following command:

```bash
python manage.py runserver
```

Open a web browser and type in http://127.0.0.1:8000/api/transfer-history/<token_id>/


This will start listening for transfer events and save them to the database. It will also fetch past events from the last 24 hours.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.


## TODOS

1. Implement a circuit breaker pattern to handle repeated failures.
2. Batch inserts to improve performance.
3. Add tests.
