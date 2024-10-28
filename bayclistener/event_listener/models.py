from django.core.exceptions import ValidationError
from django.db import models
from web3 import Web3
from web3.utils.address import to_checksum_address
from eth_utils import is_address, is_hex


def validate_address(address):
    """validate Ethereum address"""
    if not isinstance(address, str):
        return False
    try:
        # Convert to checksum address
        checksum_address = to_checksum_address(address)
        return is_address(checksum_address)
    except ValueError:
        return False 


class TransferEvent(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    tx_hash = models.CharField(max_length=255, unique=True)
    token_id = models.CharField(max_length=255)
    from_address = models.CharField(max_length=255)
    to_address = models.CharField(max_length=255)
    block_number = models.IntegerField()

    def clean(self):
        if not validate_address(self.from_address):
            raise ValidationError(
                f"'{self.from_address}' is not a valid Ethereum address"
            )
        if not validate_address(self.to_address):
            raise ValidationError(
                f"'{self.to_address}' is not a valid Ethereum address"
            )

        if not is_hex(self.tx_hash) or len(self.tx_hash) != 66 or not self.tx_hash.startswith('0x'):
            raise ValidationError(
                f"'{self.tx_hash}' is not a valid Ethereum transaction hash"
            )

        # Validate block_number is a positive integer
        if self.block_number < 0:
            raise ValidationError(f"'{self.block_number}' is not a valid block number")

    def save(self, *args, **kwargs):
        self.full_clean()  # Call the clean method before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TransferEvent {self.token_id} from {self.from_address} to {self.to_address}"
