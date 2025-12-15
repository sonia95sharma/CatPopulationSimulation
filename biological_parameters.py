"""
Enhanced biological parameters for cat population simulation
Based on detailed estrous cycle and reproductive biology
"""

from enum import Enum
from typing import Optional

class ContraceptionType(Enum):
    """Types of contraception available"""
    NONE = "none"
    SPAYED = "spayed"  # Surgical sterilization
    NEUTERED = "neutered"  # Male surgical sterilization
    AMH = "amh"  # Anti-Müllerian Hormone contraceptive

class ReproductiveStatus(Enum):
    """Female reproductive status"""
    ANESTRUS = "anestrus"  # Not cycling
    PROESTRUS = "proestrus"  # Preparing for estrus
    ESTRUS = "estrus"  # In heat, receptive
    METESTRUS = "metestrus"  # After estrus
    PREGNANT = "pregnant"  # Pregnant
    POSTPARTUM = "postpartum"  # Post-birth recovery

class BiologicalParameters:
    """Container for detailed biological parameters"""

    # Estrous cycle parameters (in days)
    ESTROUS_CYCLE_LENGTH = 21  # Days per complete cycle
    ESTRUS_LENGTH = 8  # Days female is receptive
    PROESTRUS_LENGTH = 2  # Days before estrus
    METESTRUS_LENGTH = 11  # Days after estrus (21 - 8 - 2)

    # Reproductive maturity (in days)
    FEMALE_MATURITY_MIN = 180  # 6 months
    FEMALE_MATURITY_MAX = 240  # 8 months
    MALE_MATURITY = 365  # 12 months

    # Breeding season (months when breeding does NOT occur)
    NON_BREEDING_MONTHS = [10, 11, 12]  # October, November, December

    # Male monopolization (in days) - how long male guards female
    MONOPOLIZATION_INTACT = 8  # Intact cycling females
    MONOPOLIZATION_SPAYED = 0  # Spayed females (no attraction)
    MONOPOLIZATION_AMH = 21  # AMH-treated females (full cycle)

    # Pregnancy and recovery
    GESTATION_PERIOD = 63  # Days (approximately 9 weeks)
    POSTPARTUM_DELAY = 21  # Days before can conceive again
    TOTAL_PREGNANCY_DELAY = GESTATION_PERIOD + POSTPARTUM_DELAY  # 84 days = 12 weeks

    # Litter parameters
    MEAN_LITTER_SIZE = 4.0
    SD_LITTER_SIZE = 1.5
    MAX_LITTER_SIZE = 8

    # Kitten mortality
    KITTEN_MORTALITY_LOW_DENSITY = 0.75  # 75% die before 6 months at low density
    KITTEN_MORTALITY_HIGH_DENSITY = 0.90  # 90% die at high density

    # Adult mortality (per day)
    ADULT_DAILY_MORTALITY = 0.10 / 365  # 10% annual mortality

    @classmethod
    def get_monopolization_days(cls, contraception_type: ContraceptionType) -> int:
        """Get male monopolization period based on female's contraception status"""
        if contraception_type == ContraceptionType.SPAYED:
            return cls.MONOPOLIZATION_SPAYED
        elif contraception_type == ContraceptionType.AMH:
            return cls.MONOPOLIZATION_AMH
        else:
            return cls.MONOPOLIZATION_INTACT

    @classmethod
    def is_breeding_season(cls, day_of_year: int) -> bool:
        """Check if current day is in breeding season"""
        # Convert day of year to month (approximate)
        month = (day_of_year // 30) + 1
        return month not in cls.NON_BREEDING_MONTHS

    @classmethod
    def get_female_maturity_age(cls, variation: float = 0.0) -> int:
        """
        Get female maturity age with optional variation
        variation: 0.0 = minimum (6 months), 1.0 = maximum (8 months)
        """
        age_range = cls.FEMALE_MATURITY_MAX - cls.FEMALE_MATURITY_MIN
        return cls.FEMALE_MATURITY_MIN + int(age_range * variation)


class EnhancedIndividualTraits:
    """Additional traits for enhanced biological modeling"""

    def __init__(self):
        # Estrous cycle tracking
        self.days_in_cycle = 0  # Current day in estrous cycle
        self.reproductive_status = ReproductiveStatus.ANESTRUS
        self.last_estrus_day = None

        # Pregnancy tracking
        self.pregnant = False
        self.days_pregnant = 0
        self.expected_litter_size = 0

        # Postpartum tracking
        self.days_postpartum = 0

        # Male monopolization tracking
        self.being_monopolized = False
        self.monopolizing_male_id = None
        self.days_monopolized = 0

        # Contraception details
        self.contraception_type = ContraceptionType.NONE
        self.days_on_contraception = 0

        # AMH-specific (if applicable)
        self.amh_administered = False
        self.amh_effectiveness = 1.0  # 0.0 = ineffective, 1.0 = fully effective

    def update_cycle_status(self, days_elapsed: int = 1):
        """Update reproductive cycle status"""
        if self.pregnant:
            self.days_pregnant += days_elapsed
            return

        if self.days_postpartum > 0:
            self.days_postpartum = max(0, self.days_postpartum - days_elapsed)
            if self.days_postpartum == 0:
                self.reproductive_status = ReproductiveStatus.ANESTRUS
                self.days_in_cycle = 0
            return

        # Update cycle
        self.days_in_cycle = (self.days_in_cycle + days_elapsed) % BiologicalParameters.ESTROUS_CYCLE_LENGTH

        # Determine status based on cycle day
        if self.days_in_cycle < BiologicalParameters.PROESTRUS_LENGTH:
            self.reproductive_status = ReproductiveStatus.PROESTRUS
        elif self.days_in_cycle < (BiologicalParameters.PROESTRUS_LENGTH + BiologicalParameters.ESTRUS_LENGTH):
            self.reproductive_status = ReproductiveStatus.ESTRUS
        else:
            self.reproductive_status = ReproductiveStatus.METESTRUS

    def is_receptive(self) -> bool:
        """Check if female is receptive to mating"""
        return (self.reproductive_status == ReproductiveStatus.ESTRUS and
                not self.pregnant and
                self.days_postpartum == 0)

    def can_conceive(self) -> bool:
        """Check if female can conceive"""
        if self.contraception_type in [ContraceptionType.SPAYED]:
            return False

        if self.contraception_type == ContraceptionType.AMH:
            # AMH prevents conception but allows cycling
            return False

        return self.is_receptive()

    def initiate_pregnancy(self, litter_size: int):
        """Start pregnancy"""
        self.pregnant = True
        self.days_pregnant = 0
        self.expected_litter_size = litter_size
        self.reproductive_status = ReproductiveStatus.PREGNANT

    def give_birth(self) -> int:
        """Give birth and return litter size"""
        litter_size = self.expected_litter_size
        self.pregnant = False
        self.days_pregnant = 0
        self.days_postpartum = BiologicalParameters.POSTPARTUM_DELAY
        self.reproductive_status = ReproductiveStatus.POSTPARTUM
        return litter_size


# Default parameter configuration for UI
DEFAULT_BIOLOGICAL_CONFIG = {
    # Estrous cycle
    "estrous_cycle_length": BiologicalParameters.ESTROUS_CYCLE_LENGTH,
    "estrus_length": BiologicalParameters.ESTRUS_LENGTH,

    # Maturity ages (in months for UI)
    "female_maturity_min_months": 6,
    "female_maturity_max_months": 8,
    "male_maturity_months": 12,

    # Breeding season
    "breeding_season_start_month": 1,
    "breeding_season_end_month": 9,

    # Male monopolization (in days)
    "monopolization_intact_days": BiologicalParameters.MONOPOLIZATION_INTACT,
    "monopolization_amh_days": BiologicalParameters.MONOPOLIZATION_AMH,

    # Pregnancy
    "gestation_period_days": BiologicalParameters.GESTATION_PERIOD,
    "postpartum_delay_days": BiologicalParameters.POSTPARTUM_DELAY,

    # Litter parameters
    "mean_litter_size": BiologicalParameters.MEAN_LITTER_SIZE,
    "sd_litter_size": BiologicalParameters.SD_LITTER_SIZE,
    "max_litter_size": BiologicalParameters.MAX_LITTER_SIZE,

    # Population structure (from Boone et al. 2019 paper)
    "focal_population": 50,
    "focal_carrying_capacity": 200,
    "neighborhood_population": 200,
    "neighborhood_carrying_capacity": 800,

    # Dispersal and immigration (from paper)
    "immigration_rate": 2.0,  # % per 6 months
    "dispersal_rate": 2.0,  # % per 6 months
    "litter_abandonment_per_year": 2,  # Mean litters abandoned per year
}
