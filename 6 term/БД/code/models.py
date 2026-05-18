from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, time


# ========== МОДЕЛИ ДЛЯ ТАБЛИЦ ==========

class AnimalBase(BaseModel):
    breed: str
    date_of_receipt: date
    state_of_health: str
    type: str
    id_aviary: int
    id_employee: int


class AnimalCreate(AnimalBase):
    pass


class AnimalUpdate(BaseModel):
    breed: Optional[str] = None
    date_of_receipt: Optional[date] = None
    state_of_health: Optional[str] = None
    type: Optional[str] = None
    id_aviary: Optional[int] = None
    id_employee: Optional[int] = None


class Animal(AnimalBase):
    id: int


class AviaryBase(BaseModel):
    square: float
    status: str
    type: str
    location: str


class AviaryCreate(AviaryBase):
    pass


class AviaryUpdate(BaseModel):
    square: Optional[float] = None
    status: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None


class Aviary(AviaryBase):
    id: int


class EmployeeBase(BaseModel):
    snp: str
    telephone: str
    hire_date: date
    post: str


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    snp: Optional[str] = None
    telephone: Optional[str] = None
    hire_date: Optional[date] = None
    post: Optional[str] = None


class Employee(EmployeeBase):
    id: int


class VolunteerBase(BaseModel):
    snp: str
    telephone: str
    email: str
    duty: str


class VolunteerCreate(VolunteerBase):
    pass


class VolunteerUpdate(BaseModel):
    snp: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    duty: Optional[str] = None


class Volunteer(VolunteerBase):
    id: int


class AdoptiveParentBase(BaseModel):
    snp: str
    telephone: str
    approval_status: str
    address: str


class AdoptiveParentCreate(AdoptiveParentBase):
    pass


class AdoptiveParentUpdate(BaseModel):
    snp: Optional[str] = None
    telephone: Optional[str] = None
    approval_status: Optional[str] = None
    address: Optional[str] = None


class AdoptiveParent(AdoptiveParentBase):
    id: int


class MedicalProcedureBase(BaseModel):
    cost: int
    amount: int
    reason: str
    name: str


class MedicalProcedureCreate(MedicalProcedureBase):
    pass


class MedicalProcedureUpdate(BaseModel):
    cost: Optional[int] = None
    amount: Optional[int] = None
    reason: Optional[str] = None
    name: Optional[str] = None


class MedicalProcedure(MedicalProcedureBase):
    id: int


class FeedSupplyBase(BaseModel):
    quantity: int
    delivery_date: date
    the_supplier: str
    type_of_feed: str


class FeedSupplyCreate(FeedSupplyBase):
    pass


class FeedSupplyUpdate(BaseModel):
    quantity: Optional[int] = None
    delivery_date: Optional[date] = None
    the_supplier: Optional[str] = None
    type_of_feed: Optional[str] = None


class FeedSupply(FeedSupplyBase):
    id: int


# ========== СВЯЗУЮЩИЕ ТАБЛИЦЫ ==========

class AdoptiveAnimalBase(BaseModel):
    id_adoptive: int
    id_animal: int


class AdoptiveAnimalCreate(AdoptiveAnimalBase):
    pass


class AdoptiveAnimal(AdoptiveAnimalBase):
    id: int


class AnimalVolunteerBase(BaseModel):
    id_volunteer: int
    id_animal: int


class AnimalVolunteerCreate(AnimalVolunteerBase):
    pass


class AnimalVolunteer(AnimalVolunteerBase):
    id: int


class AnimalFeedSupplyBase(BaseModel):
    id_animal: int
    id_feed_supply: int


class AnimalFeedSupplyCreate(AnimalFeedSupplyBase):
    pass


class AnimalFeedSupply(AnimalFeedSupplyBase):
    id: int


class AnimalMedicalProcedureBase(BaseModel):
    id_animal: int
    id_medical: int
    procedure_date: Optional[date] = None


class AnimalMedicalProcedureCreate(AnimalMedicalProcedureBase):
    pass


class AnimalMedicalProcedure(AnimalMedicalProcedureBase):
    id: int


# ========== МОДЕЛИ ДЛЯ ФИЛЬТРАЦИИ ==========

class FilterParams(BaseModel):
    """Модель для параметров фильтрации"""
    id: Optional[int] = None
    type: Optional[str] = None
    breed: Optional[str] = None
    state_of_health: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    post: Optional[str] = None
    hire_date_from: Optional[str] = None
    hire_date_to: Optional[str] = None
    aviary_status: Optional[str] = None
    aviary_type: Optional[str] = None
    min_square: Optional[float] = None
    max_square: Optional[float] = None
    duty: Optional[str] = None
    min_cost: Optional[int] = None
    max_cost: Optional[int] = None
    procedure_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "type": "Кошка",
                "state_of_health": "Здоров",
                "breed": "Британская короткошерстная"
            }
        }


# ========== МОДЕЛИ ДЛЯ ОТВЕТОВ ==========

class ResponseModel(BaseModel):
    message: str
    data: Optional[List] = None


class PaginatedResponse(BaseModel):
    data: List
    pagination: dict
    filters_applied: dict