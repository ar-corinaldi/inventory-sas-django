from abc import ABC, abstractmethod
from typing import Any
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Sum


class InventoryTransactionStrategy(ABC):

    inventory_transaction: Any = None

    def __init__(self, inventory_transaction) -> None:
        self.inventory_transaction = inventory_transaction
        super().__init__()

    @abstractmethod
    def clean(self):
        pass

    @abstractmethod
    def execute_order_items(self):
        pass

    # TODO: mark as abstract and make corrections of implementation

    def execute_product_movement(self):
        if self.inventory_transaction.is_inbound:
            self._execute_product_movement_inbound()
        else:
            self._execute_product_movement_outbound()

    # TODO: mark as abstract and move implementation to Remission and Devolution
    def execute_inventory_movement(self):
        from inventorySAS.models import Inventory
        origin = self.inventory_transaction.origin
        destination = self.inventory_transaction.destination

        inventory_origin, created = Inventory.objects.get_or_create(
            product=self.inventory_transaction.product,
            warehouse=origin,
            defaults={'quantity': 0,
                      'tenant': self.inventory_transaction.tenant}
        )
        inventory_origin.quantity -= self.inventory_transaction.quantity
        inventory_origin.save()

        inventory_destination, created = Inventory.objects.get_or_create(
            product=self.inventory_transaction.product,
            warehouse=destination,
            defaults={'quantity': self.inventory_transaction.quantity,
                      'tenant': self.inventory_transaction.tenant}
        )
        if not created:
            inventory_destination.quantity += self.inventory_transaction.quantity

        inventory_destination.save()

    def _clean_sell_or_obsolete(self):
        inventory_transaction = self.inventory_transaction
        if inventory_transaction.origin is None:
            raise ValidationError(_('There is no origin'))

        if not inventory_transaction.origin.is_owned:
            raise ValidationError(_('Origin must be owned'))

        inventory_transaction.destination = None
        inventory_transaction.is_inbound = False

    def _execute_inventory_movement_outbound(self):
        from inventorySAS.models import Inventory
        origin = self.inventory_transaction.origin
        inventory_origin = Inventory.objects.get(
            product=self.inventory_transaction.product,
            warehouse=origin
        )
        if inventory_origin is None:
            raise ValidationError(
                _('There should always be a origin in the current movement type'),
            )

        inventory_origin.quantity -= self.inventory_transaction.quantity
        inventory_origin.save()

    def _execute_product_movement_outbound(self):
        inventory_transaction = self.inventory_transaction
        inventory_transaction.product.quantity -= inventory_transaction.quantity
        inventory_transaction.product.save()

    def _execute_product_movement_inbound(self):
        inventory_transaction = self.inventory_transaction
        inventory_transaction.product.quantity += inventory_transaction.quantity
        inventory_transaction.product.save()

    def _execute_order_item_transport_if_exists(self):
        from inventorySAS.models import InvoiceItem, InvoiceItemType
        inv_transaction = self.inventory_transaction
        if inv_transaction.transport is None:
            return
        InvoiceItem(order=inv_transaction.order,
                    inventory_transaction=inv_transaction,
                    date=inv_transaction.date,
                    item_name=f'Transporte vehículo: {inv_transaction.transport.vehicle}',
                    order_item_type=InvoiceItemType.TRANSPORT,
                    quantity=0,
                    price=inv_transaction.transport.price,
                    total=inv_transaction.transport.price).save()


class BuyStrategy(InventoryTransactionStrategy):

    def execute_inventory_movement(self):
        from inventorySAS.models import Inventory
        destination = self.inventory_transaction.destination
        inventory_destination, created = Inventory.objects.get_or_create(
            product=self.inventory_transaction.product,
            warehouse=destination,
            defaults={'quantity': self.inventory_transaction.quantity,
                      'tenant': self.inventory_transaction.tenant}
        )

        if not created:
            inventory_destination.quantity += self.inventory_transaction.quantity
        inventory_destination.save()

    def execute_product_movement(self):
        return super().execute_product_movement()

    def clean(self):
        inventory_transaction = self.inventory_transaction
        if inventory_transaction.order is None:
            raise ValidationError(_('Order must be mandatory for buying'))

        if inventory_transaction.destination is None:
            raise ValidationError(_('Destination is mandatory for buying'))

        if not inventory_transaction.destination.is_owned:
            raise ValidationError(_('Destination must be owned for buying'))

        inventory_transaction.is_inbound = True
        return super().clean()

    def execute_order_items(self):
        from inventorySAS.models import InvoiceItem, InvoiceItemType
        inv_transaction = self.inventory_transaction
        InvoiceItem(
            order=inv_transaction.order,
            inventory_transaction=inv_transaction,
            date=inv_transaction.date,
            item_name=inv_transaction.product.name,
            order_item_type=InvoiceItemType.BUY,
            quantity=inv_transaction.quantity,
            price=inv_transaction.product.buy_price,
            total=inv_transaction.product.buy_price*inv_transaction.quantity
        ).save()

        self._execute_order_item_transport_if_exists()


class SellStrategy(InventoryTransactionStrategy):

    def execute_inventory_movement(self):
        # validate price
        return super()._execute_inventory_movement_outbound()

    def execute_product_movement(self):
        return super().execute_product_movement()

    def clean(self):
        inventory_transaction = self.inventory_transaction
        if inventory_transaction.order is None:
            raise ValidationError(
                _('Order must be mandatory for selling'))

        return super()._clean_sell_or_obsolete()

    def execute_order_items(self):
        from inventorySAS.models import InvoiceItem, InvoiceItemType
        inv_transaction = self.inventory_transaction
        InvoiceItem(
            order=inv_transaction.order,
            inventory_transaction=inv_transaction,
            date=inv_transaction.date,
            item_name=inv_transaction.product.name,
            quantity=inv_transaction.quantity,
            price=inv_transaction.product.sell_price,
            total=inv_transaction.product.sell_price*inv_transaction.quantity
        ).save()

        self._execute_order_item_transport_if_exists()


class ObsoleteStrategy(InventoryTransactionStrategy):

    def execute_inventory_movement(self):
        # validate no price
        return super()._execute_inventory_movement_outbound()

    def execute_product_movement(self):
        return super().execute_product_movement()

    def clean(self):
        self.inventory_transaction.order = None
        return super()._clean_sell_or_obsolete()

    def execute_order_items(self):
        pass


class RemissionStrategy(InventoryTransactionStrategy):
    def clean(self):
        inventory_transaction = self.inventory_transaction
        if inventory_transaction.order is None:
            raise ValidationError(_('Order must be mandatory for remission'))

        if inventory_transaction.origin is None:
            raise ValidationError(_('Origin must be mandatory for remission'))

        if not inventory_transaction.origin.is_owned:
            raise ValidationError(_('Origin must be owned for devolution'))

        if inventory_transaction.destination is None:
            raise ValidationError(
                _('Destination must be mandatory for remission'))

        if inventory_transaction.destination.is_owned:
            raise ValidationError(
                _('Destination cannot be owned in remission'))

        inventory_transaction.is_inbound = False
        return super().clean()

    def __generate_outbound_transaction(self):
        from inventorySAS.models import OutboundTransaction
        outbound = OutboundTransaction(
            outbound_transaction=self.inventory_transaction,
            quantity_left=self.inventory_transaction.quantity,
            order=self.inventory_transaction.order,
            tenant=self.inventory_transaction.tenant)
        outbound.save()

    def execute_order_items(self):
        self.__generate_outbound_transaction()
        self._execute_order_item_transport_if_exists()


class DevolutionStrategy(InventoryTransactionStrategy):
    def clean(self):
        inventory_transaction = self.inventory_transaction

        sum_dict = inventory_transaction.order.outboundtransaction_set.filter(outbound_transaction__product=inventory_transaction.product,
                                                                              outbound_transaction__date__lte=inventory_transaction.date).aggregate(Sum('quantity_left'))
        print('randommness', sum_dict, inventory_transaction.quantity)
        if sum_dict.get('quantity_left__sum') < inventory_transaction.quantity:
            raise ValidationError(
                _('There are not enough items in the destination en la fecha dada'))

        if inventory_transaction.order is None:
            raise ValidationError(
                _('Order must be mandatory for rent devolution'))

        if inventory_transaction.origin is None:
            raise ValidationError(_('Origin must be mandatory for devolution'))

        if inventory_transaction.destination is None:
            raise ValidationError(
                _('Destination must be mandatory for devolution'))

        if not inventory_transaction.destination.is_owned:
            raise ValidationError(
                _('Destination must be owned for devolution'))

        inventory_transaction.is_inbound = True
        return super().clean()

    def __generate_order_transactions(self):
        from inventorySAS.models import InvoiceTransaction, MovementType

        inventory_transaction = self.inventory_transaction
        outbound_transactions = inventory_transaction.order.outboundtransaction_set.filter(
            outbound_transaction__product=inventory_transaction.product,
            outbound_transaction__date__lte=inventory_transaction.date,
            outbound_transaction__movement_type=MovementType.REMISSION,
            quantity_left__gt=0).order_by('outbound_transaction__date')

        incoming_quantity = inventory_transaction.quantity
        if len(outbound_transactions) == 0:
            raise ValidationError('There is no prior remissions remaining')

        for outbound_inventory_transaction in outbound_transactions:
            outbound = outbound_inventory_transaction

            current_outbound_quantity_left = outbound.quantity_left
            new_outbound_quantity_left = current_outbound_quantity_left - \
                incoming_quantity  # quantity for the outbound to be left
            # quantity used for the order transaction
            quantity_used = min(
                current_outbound_quantity_left, incoming_quantity)
            incoming_quantity -= quantity_used

            if new_outbound_quantity_left < 0:
                new_outbound_quantity_left = 0

            outbound.quantity_left = new_outbound_quantity_left
            outbound.save()
            new_order_transaction = InvoiceTransaction(
                outbound=outbound,
                inbound_inventory=inventory_transaction,
                product=inventory_transaction.product,
                start_date=outbound.outbound_transaction.date,
                end_date=inventory_transaction.date,
                order=inventory_transaction.order,
                quantity=quantity_used
            )

            new_order_transaction.save()

            has_quantity_left = incoming_quantity > 0
            if not has_quantity_left:
                break

    def execute_order_items(self):
        self.__generate_order_transactions()
        self._execute_order_item_transport_if_exists()


class AdminStrategy(InventoryTransactionStrategy):
    def execute_inventory_movement(self):
        from inventorySAS.models import Inventory
        destination = self.inventory_transaction.destination
        inventory_destination, created = Inventory.objects.get_or_create(
            product=self.inventory_transaction.product,
            warehouse=destination,
            defaults={'quantity': self.inventory_transaction.quantity,
                      'tenant': self.inventory_transaction.tenant}
        )

        if not created:
            inventory_destination.quantity += self.inventory_transaction.quantity
        inventory_destination.save()

    def execute_product_movement(self):
        return super().execute_product_movement()

    def clean(self):
        inventory_transaction = self.inventory_transaction

        if inventory_transaction.order is not None:
            raise ValidationError(_('Order is mandatory for admin'))
        if inventory_transaction.destination is None:
            raise ValidationError(_('Destination is mandatory for admin'))
        if not inventory_transaction.destination.is_owned:
            raise ValidationError(_('Destination must be owned for admin'))

        inventory_transaction.origin = None
        inventory_transaction.is_inbound = True
        return super().clean()

    def execute_order_items(self):
        pass


class RepositionStrategy(InventoryTransactionStrategy):
    def execute_product_movement(self):
        return super().execute_product_movement()

    def __clean_and_save_devolution(self):
        from inventorySAS.models import MovementType
        inventory_transaction = self.inventory_transaction
        inventory_transaction.movement_type = MovementType.DEVOLUTION
        inventory_transaction.clean()
        inventory_transaction.save()

    '''
    Una reposición genera un devolución del inventario y luego si crea la reposición
    '''

    def execute_inventory_movement(self):

        try:
            from inventorySAS.models import MovementType
            inventory_transaction = self.inventory_transaction

            self.__clean_and_save_devolution()
            inventory_transaction.movement_type = MovementType.REPOSITION
            inventory_transaction.origin, inventory_transaction.destination = inventory_transaction.destination, inventory_transaction.origin
            inventory_transaction.is_inbound = False
            inventory_transaction.id = None
            self._execute_inventory_movement_outbound()
        # except ValidationError:
        #     if ValidationError is None or ValidationError.message is None:
        #         raise ValidationError('There has been an unkown error')
        #     raise ValidationError(ValidationError.message)
        except:
            raise ValidationError('There has been an unkown error')

    # Este realiza la logica de Devolucion crea la entrada de devolucion y añade un nueva entrada de reposicion

    def clean(self):
        pass

    def execute_order_items(self):
        from inventorySAS.models import InvoiceItem
        inv_transaction = self.inventory_transaction
        InvoiceItem(
            order=inv_transaction.order,
            inventory_transaction=inv_transaction,
            date=inv_transaction.date,
            item_name=inv_transaction.product.name,
            quantity=inv_transaction.quantity,
            price=inv_transaction.product.reposition_price,
            total=inv_transaction.product.reposition_price*inv_transaction.quantity
        ).save()

        self._execute_order_item_transport_if_exists()


class SpareStrategy(InventoryTransactionStrategy):
    def execute_product_movement(self):
        return super().execute_product_movement()

    def execute_inventory_movement(self):
        return super()._execute_product_movement_inbound()

    def clean(self):
        inventory_transaction = self.inventory_transaction
        inventory_transaction.is_inbound = True
        if inventory_transaction.origin is None:
            raise ValidationError(_('Origin is mandatory'))
        if not inventory_transaction.origin.is_owned:
            raise ValidationError(_('Origin must be owned'))

        return super().clean()

    def execute_order_items(self):
        pass


class MissingStrategy(InventoryTransactionStrategy):
    def execute_product_movement(self):
        return super()._execute_product_movement_outbound()

    def execute_inventory_movement(self):
        return super()._execute_inventory_movement_outbound()

    def clean(self):
        inventory_transaction = self.inventory_transaction
        inventory_transaction.is_inbound = False
        if inventory_transaction.origin is None:
            raise ValidationError(_('Origin is mandatory'))
        if not inventory_transaction.origin.is_owned:
            raise ValidationError(_('Origin must be owned'))
        return super().clean()

    def execute_order_items(self):
        pass


class TransferStrategy(InventoryTransactionStrategy):
    def execute_product_movement(self):
        pass

    def execute_inventory_movement(self):
        return super().execute_inventory_movement()

    def clean(self):
        inventory_transaction = self.inventory_transaction

        if inventory_transaction.destination is None:
            raise ValidationError(_('Destination is mandatory for admin'))

        if not inventory_transaction.destination.is_owned:
            raise ValidationError(_('Destination must be owned'))

        if inventory_transaction.origin is None:
            raise ValidationError(_('Origin is mandatory for admin'))
        if not inventory_transaction.origin.is_owned:
            raise ValidationError(_('Origin must be owned'))

        inventory_transaction.is_inbound = True
        return super().clean()

    def execute_order_items(self):
        pass
