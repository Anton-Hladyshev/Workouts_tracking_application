from enum import Enum


class TrainingType(str, Enum): # Enum for training type
    INDIVIDUAL = "individual"
    GROUP = "group"

class Discipline(str, Enum): # Enum for discipline
    MMA = "MMA"
    STRIKING = "striking"
    BOXE_FEMININ = "boxe_feminin"
    WRESTLING = "wrestling"
    BJJ = "BJJ"
    PHISICAL_PREPARATION = "physical_preparation"

class Role(str, Enum): # Enum for user role
    COACH = "coach"
    STUDENT = "student"

class UserType(str, Enum):
    COMPETITOR = "competitor"
    NON_COMPETITOR = "non_competitor"
    BEGINNER = "beginner"

class Gender(str, Enum):
    M = "men"
    W = "woman"

class Auditory(str, Enum):
    CHILDREN = "children"
    ADULTS = "adults"
    SENIORS = "seniors"