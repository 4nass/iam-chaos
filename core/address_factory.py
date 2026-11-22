
import random
from faker import Faker
from core.address_builder import AddressBuilder, AddressType

class AddressFactory:
    @staticmethod
    def create_address(locale="fr_FR"):
        """Create an address generator for the supported locale."""
        if locale != "fr_FR":
            raise ValueError(f"Unsupported locale : {locale}")
        return FrenchAddress()

class FrenchAddress:
    def generate(self):
        builder = AddressBuilder()
        fake = Faker(['fr_FR'])
        address = (builder.add_type(random.choice(list(AddressType)))
                   .add_street_number(fake.building_number())
                   .add_complement_street_number(random.choice(['bis', 'ter', 'quater']) if random.random() > 0.8 else '')
                   .add_street_type(random.choice(['boulevard', 'avenue', 'rue', 'place', 'chemin']))
                   .add_street_name(fake.street_name().split(' ', 1)[1])
                   .add_complement_location('Batiment 1')
                   .add_complement_identification('')
                   .add_complement_address('BP 12345')
                   .add_postal_code(fake.postcode())
                   .add_locality(fake.city())
                   .add_region(fake.region())
                   .add_country('France'))
        return address
